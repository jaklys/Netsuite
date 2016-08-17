"""
Class for control of the Metec DVM
metex.py (C) J.M.,rev.28-Oct-15
"""
copyr = 'metex.py (C) J.M.,rev.28-Oct-15'
port = 'COM1'       #default port for selftest

import sys, time
import serial

class Metex:
    """
    DVM uses 1200Bd UART communication 7 + 1 bit.
    !!! Run Python as administrator else SerialException in write fires!!!
    """
    def __init__(self, port, timeout):
        """
        Constructor stores required timeout and COM port
        """
        self.port = port
        self.timeout = timeout      #default timeout value
        self.handle = None
    
    def open(self):
        """
        Initiate COM port provided to constructor
        Input:  none
        Output: True if OK, raises exception if failed
        """
        try:
            self.handle = serial.Serial(self.port, baudrate = 1200,
                   bytesize = 7, timeout = self.timeout,
                   rtscts = False, dsrdtr = False)
            self.handle.setDTR(True)
            self.handle.setRTS(False)
        except Exception:
            print('Metex: COM port opening failed !')
            raise
        print('Metex: ' + port + ' opened.')
        return True

    def close(self):
        """
        Close handle
        Input:  None
        Returns:True if OK, raises exception if fails
        """
        if self.handle != None:
            try:
                self.handle.close()
                self.handle = None
                print('Metex: ' + port + ' closed.')
            except Exception:
                print('Exception in Metex.close() !')
                raise
        return True

    def read(self):
        """
        Reads the DVM: Sends the 'D' command and waits for response
        Returned string converted to float
        Input:  none
        Return: None if error or timeout
                float voltage if OK
        """
        cmd = 'D'
        cmd = cmd.encode()
        try:
            self.handle.write(cmd)
            resp = self.readResponse()
        except Exception:
            print('Metex.read() exception !')
            raise
        if resp == 'timeout':
            print('Metex.read() timeout !')
            return None
        return resp
    
    def readResponse(self):
        """
        Reads command response until terminal '\n' detected
        Input:  None
        Return: reply as bytes
                'timeout' if expected '\n' didn't come within specified time
        """
        startTime = time.time()
        response = b''      #empty
        while time.time() < startTime + self.timeout:
            resl = self.handle.read()   #read character
            response = response + resl
            if resl == b'\r':
                break
        else:       #exit without break - timeout
            return 'timeout'
        response = response.decode()   #convert to string
        #convert to float        
        response = response.strip()
        volt = float(response[2:9])
        unit = response[9:]
        if unit == 'mV':
            volt /= 1000.
        return volt

    def clrBuffer(self):
        """
        Clears UART input buffer
        Input:  none
        Return: none
        """
        try:
            self.handle.flushInput()
        except Exception:
            print('Metex.clrBuffer() exception !')
            raise
            
# Selftest
#==========
if __name__ == '__main__':      #self test   
    print(copyr) 
    try:
        dvm = Metex(port, 1)    #create device class instance
        dvm.open()
    except Exception:
        raise
        sys.exit(2)
        
    curTime = 0
    stepTime = 2
    try:
        for i in range(10):
            volt = dvm.read()
            if volt == None:
                print('Reading failed - terminated !')
                break
            print('%d %.3f' % (curTime, volt))
            time.sleep(stepTime)        
            curTime += stepTime
    except Exception:
        raise       #leave default handler to process exception
    finally:        #clean up in any case to prevent memory leaks
        try:
            dvm.close()     
        except Exception:
            reslt = False
    
