# python-serial-ntp
This is a simple python implementation of the NTP protocol that uses serial radio modules as the communication medium. The notebooks are pretty self explanatory.
![An example application for synchronizing two raspberry pi computers.](/doc/opening_figure.jpg)

## Requirements
This project relys on pyserial for communication and adjtimex for adjusting the clock. Other requirements are numpy, jupyterplot for computation and visualization purposes. This project requires python 3.8 or newer to work.
## Performance
Using this simple program and a set of Holybro telemetry modules, a sub-millisecond synchronization accuracy between a raspberry Pi 4 and laptop was achieved.
