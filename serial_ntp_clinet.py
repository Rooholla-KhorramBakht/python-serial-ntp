import serial
import time
import struct
import threading
import time 
import numpy as np
import multiprocessing
import subprocess


def adjtSpeed(tick):
    '''A fuction that calls the adjtimex system command (install is with apt-get) to slow down or speed up the clock.'''
    if tick > 10:
        tick = 10
    elif tick <-10:
        tick = -10        
    subprocess.Popen(['sudo', '/sbin/adjtimex', f'-t', f'{10000+tick}'],stdout=subprocess.PIPE)
    
def setClock(time_sec, time_usec):
    '''A function that calls a custo C program that sets the current time'''
    subprocess.Popen(['sudo', '/home/pi/python-serial-ntp/setclock', f'{time_sec}', f'{time_usec}'],stdout=subprocess.PIPE)


class serialNtpClient():
    '''A class that implements the NTP client with serial interface. This has been tested with SiK serial radio modules'''
    def __init__(self, tr_scale = 0.5, port = '/dev/ttyUSB0', baudRate = 57600, transmit_rate = 5, record = False, plot = False):
        '''
        The constructor of the class. With this, the NTP also starts
        @param tr_scale:
        The asymetry between transmission and reception of packets. It is 0.5 for symetrical communication
        or it can be identified by recording a dataset (Explained later)
        @param: port:
        The serial ID of the serial port we want to use for the client (The port representing the radio module)
        @param: baudRate:
        The communication boadrate of the serial interface
        @param: record:
        A boolian flag that dteremins if we want the live plots and the dataset to be shown and recorded
        @param: transmit_rate:
        How often to we want to communicate with the server for synchronization
        @param: plot:
        Do we want a plot of the skew over time (for debugging)
        '''
        self.transmit_rate = transmit_rate #The frequency of running the NTP stack (Querying time from the Server)
        self.port = serial.Serial(port ,baudRate, timeout = 2)#1.0/self.transmit_rate)        
        self.record = record
        self.running = True
        self.plot = plot
        self.receiveTread = threading.Thread(target=self.receivingThread, args=())
        self.queryThread = threading.Thread(target=self.queryThreadFunc, args=())
        self.receiveTread.start()
        self.queryThread.start()
        self.tr_scale = tr_scale # The realtive scale between transmitting a packet and receiving it
        self.moving_window = []
        # For identification purposes, we can record the timestamps used for running the NTP algorithm
        if self.record:
            self.dataset = []
        
    def receivingThread(self):
        '''A thread that handles the responses from the server'''
        while self.running:
            data = self.port.read(24)
            if len(data) == 24:
                self.stamp4 = time.time_ns() #Response time stamp
                self.stamp1, self.stamp2, self.stamp3 = struct.unpack('3Q',data)
                #compute the round trip time 
                #(the time that takes for the packet to get to the server and for the response to be received)
                delta = np.array((self.stamp4-self.stamp1)-(self.stamp3-self.stamp2))
                #The estimated server time at the instance of receiving the response from the server (stamp4)
                server_time  = self.stamp3 + self.tr_scale*delta
                #The clock skew of the client with respect to the server
                skew_ns = (self.stamp3-self.stamp4) + self.tr_scale*delta
                #if the clock skew is larger than 100 ms, forcefully set the clock to the server time
                if abs(skew_ns*1e-6) > 100:
                    print(f'Too large time shift ({abs(skew_ns*1e-6)} ms), Setting the time')
                    setClock(int(server_time*1e-9),int((server_time*1e-9-int(server_time*1e-9))*1e6))
                #Store the skew valu in the moving average list (for reducing estimation noise)    
                self.moving_window.append(skew_ns*1e-9)
                #when the communication link is inconsistent, we can have outlier estimates added to the 
                #moving averaging list. In such cases, the variance grows large thus, we should discard the
                #list and start again
                if np.var(self.moving_window)>1:
                    print('Inconsistent communicaiton, clearning the averaging buffer...')
                    self.moving_window = []
                #If there are enough samples in the list, bagin the clock adjustment process by 
                #Slowing down the system clock when we're ahead of the server clock and speeding it up
                #when we are behind.
                if len(self.moving_window) > 100 and not self.record:
                    skew = np.mean(self.moving_window)
                    skew_us = int((skew-int(skew))*1e6)

                    error_ms = skew_us/1000.0
                    #error times a Kp compensation gain
                    tick = error_ms*1 
                    adjtSpeed(tick)
                    #remove the oldest sample from the list
                    del(self.moving_window[0])
                    #print the skew (for debugging)
                    print(skew_us/1000.0)
                #record the raw stamps for calibration purposes
                if self.record:
                    self.dataset.append([self.stamp1, self.stamp2, self.stamp3, self.stamp4])
                
    def queryThreadFunc(self):
        '''A thread that periodically transmits requests to the server '''
        while self.running:
            payload = struct.pack('Q', time.time_ns())
            self.port.write(payload)
            time.sleep( 1.0/self.transmit_rate )
              
    def clientStop(self):
        self.running = False
        self.receiveTread.join()
        self.transmitTread.join()
        self.port.close()
        
        
client = serialNtpClient(0.5566459128784326)
