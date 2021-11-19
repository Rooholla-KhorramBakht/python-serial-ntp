import serial
import time
import struct
import threading
import time 
import numpy as np
import multiprocessing

class serialNtpClient():
    def __init__(self, tr_scale = None, port = '/dev/ttyUSB1', baudRate = 57600, record = False):
        
        self.transmit_rate = 1
        self.port = serial.Serial(port ,baudRate, timeout = 2)#1.0/self.transmit_rate)        
        self.record = record
        self.running = True
        self.receiveTread = threading.Thread(target=self.receivingThread, args=())
        self.queryThread = threading.Thread(target=self.queryThreadFunc, args=())
        self.receiveTread.start()
        self.queryThread.start()
        self.dataset = []
        self.tr_scale = tr_scale
        self.moving_window = []
        
        
    def receivingThread(self):
        while self.running:
            data = self.port.read(24)
            if len(data) == 24:
                self.stamp4 = time.time_ns()
                self.stamp1, self.stamp2, self.stamp3 = struct.unpack('3Q',data)
                delta = np.array((self.stamp4-self.stamp1)-(self.stamp3-self.stamp2))
#                 skew = np.array(self.stamp3-self.stamp4).astype(np.float64) + self.tr_scale*delta
                server_time  = self.stamp3 + self.tr_scale*delta
                skew_ns = (self.stamp3-self.stamp4) + self.tr_scale*delta
                if skew_ns*1e-9 > 1:
                    print('Setting time')
                    time.clock_settime_ns(0,int(server_time))
#                 self.moving_window.append(skew*1e-9)
#                 if len(self.moving_window) > 200:
#                     del(self.moving_window[0])
                print(f'{int(skew_ns*1e-9)}')
                print(f'{int(server_time)}')
#                 print(f'{np.mean(self.moving_window)*1000:.2f}')
                if self.record:
                    self.dataset.append([self.stamp1, self.stamp2, self.stamp3, self.stamp4])
                
    def queryThreadFunc(self):
        while self.running:
#             payload = struct.pack('Q4c', time.time_ns(), b'a',b'b',b'c',b'\n')
            payload = struct.pack('Q', time.time_ns())
            self.port.write(payload)
#             print(f'sending: {len(payload)}')
            time.sleep( 1.0/self.transmit_rate )
              
    def clientStop(self):
        self.running = False
        self.receiveTread.join()
#         self.transmitTread.join()
        self.port.close()
        
client = serialNtpClient(0.5566459128784326)
