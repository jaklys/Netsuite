""" 
Class for Agilent U2722A source meter control under VISA
and Agilent IO Library
csrc2722.py (C) J.M.,rev.5-Feb-16
"""
copyr = 'csrc2722.py (C) J.M.,rev.5-Feb-16'
srcName = '2722A'    #default VISA name for self test

import sys, time
import visa
# import visasim as visa     #simulator 

class Src2722:
    """
    Class implementing SCPI control of Agilent U2722A source meter
    control via Agilent IO Libraries and VISA interface
    """
    def __init__(self, rm, visaName):
        """
        Constructor registers the visa name and resource manager handle
        as class attributes. Resource manager handle has to be fetched
        before class instance created.
        Initiates the device handle to None
        Input:  rm - resource manager to be stored as class attribute
                visaName - VISA address to be stored
        """
        self.rm = rm
        self.visaName = visaName
        self.handle = None
        
    def open(self):
        """
        Connects to U2722 device with VISA name given at construction,
        Brings the device to default state, sets ASCII output format.
        Input:  none
        Output: True if OK, raises exception if failed
        """
        try:
            self.handle = self.rm.get_instrument(self.visaName)
            self.handle.write('*RST')   #reset device to default
            time.sleep(.5)
        except Exception:
            print('Src2722.open() failed !')
            raise
        return True

    def close(self):
        """
        Brings the device back to default state using *RST,
        closes device handle
        Input:   None
        Returns: True if OK, raises exception if fails   
        """
        if self.handle != None:
            try:
                self.handle.write('*RST')
                self.handle.close()
                self.handle = None
            except Exception:
                print('Src2722.close() failed !')
                raise
        return True
    
    def setVoltage(self, channel, voltage):
        """ 
        Set channel voltage to given value. Keeps actual channel configuration.
        Input:  inst - instrument handle
                channel - supply channel 1 - 3
                voltage - required voltage in V
        Returns:True if OK, False if invalid channel,
                raises exception if failed
        """
        strChnl = self.checkChannel(channel)
        if not strChnl:
            return False
        try:
            cmd = 'VOLT ' + str(voltage) + ', ' + strChnl
            self.handle.write(cmd)     #sets sampling period
        except Exception:
            print('Src2722.setVoltage() failed !')
            raise
        return True

    def setCurrent(self, channel, current):
        """ 
        Set channel current to given value. Keeps actual channel configuration.
        Input:  inst - instrument handle
                channel - supply channel 1 - 3
                current - required current in A
        Returns:True if OK, False if invalid channel,
                raises exception if failed
        """
        strChnl = self.checkChannel(channel)
        if not strChnl:
            return False
        try:
            cmd = 'CURR ' + str(current) + ', ' + strChnl
            self.handle.write(cmd)     #sets sampling period
        except Exception:
            print('Src2722:setCurrent() failed !')
            raise
        return True    
        
    def enableOutput(self, channel, state):
        """ 
        Switch source output on
        Input:   channel - 1 to 3
                 state - True on, False - off
        Returns: True if OK, False if invalid channel,
                 raises exceptionif didn't succeed
        """
        strChnl = self.checkChannel(channel)
        if not strChnl:
            return False

        if state:
            cmd = 'OUTP 1, '
        else:
            cmd = 'OUTP 0, '
        cmd = cmd + strChnl
        try:
            self.handle.write(cmd)
        except Exception:
            print('Src2722.setOutput() set state failed !')        
            raise    
        return True      

    currRanges = ((1e-6, 'R1uA'), (1e-5, 'R10uA'), (1e-4, 'R100uA'),
                  (1e-3, 'R1mA'), (.01, 'R10mA'), (0.12, 'R120mA'))
    
    def configVoltSrc(self, channel, volt, currLimit):
        """
        Configure channel as voltage source.
        Selects automatically current and voltage ranges.
        Input:  channel - 1 to 3
                volt - float, voltage in V
                currLimit - float, maximum provided current
        Returns:True if OK, False if invalid channe or current range,
                raises exception if failed
        """
        strChnl = self.checkChannel(channel)
        if not strChnl:
            return False

        for crange in self.currRanges:
            if currLimit <= crange[0]:
                strRange = crange[1]
                break;
        else:   # range exceeds maximum available
            print('Src2722.configSrc() invalid current range !')
            return False
        #Checks OK - send setting commands
        try:
            if abs(volt) <= 2.:
                cmd = 'VOLT:RANG R2V, '
            else:
                cmd = 'VOLT:RANG R20V, '
            cmd += strChnl
            self.handle.write(cmd)
            
            cmd = "VOLT " + str(volt) + ',' + strChnl
            self.handle.write(cmd)

            cmd = "CURR:RANG " + strRange + ',' + strChnl            
            self.handle.write(cmd)

            cmd = "CURR:LIM " + str(currLimit) + ',' + strChnl            
            self.handle.write(cmd)
        except Exception:
            print('Src2722.config() sending configuration failed !')
            raise
        return True

    def configCurrSrc(self, channel, current, voltLimit):
        """
        Configure channel as voltage source
        Selects automatically current and voltage ranges.
        Input:  channel - 1 to 3
                current - float, voltage in A
                currRange - float, the closest higher range selected
                currLimit - float, maximum provided current
        Returns:True if OK, False if invalid channel or current range
                raises exception if failed
        """
        strChnl = self.checkChannel(channel)
        if not strChnl:
            return False
        
        for crange in self.currRanges:
            if abs(current) <= crange[0]:
                strRange = crange[1]
                break;
        else:   # range exceeds maximum available
            print('Src2722.configSrc() invalid current range !')
            return False
        #Checks OK - send setting commands
        try:
            cmd = "CURR:RANG " + strRange + ',' + strChnl            
            self.handle.write(cmd)

            if abs(voltLimit) <= 2.:
                cmd = 'VOLT:RANG R2V, '
            else:
                cmd = 'VOLT:RANG R20V, '
            cmd += strChnl
            self.handle.write(cmd)
            
            cmd = "VOLT:LIM " + str(voltLimit) + ',' + strChnl
            self.handle.write(cmd)

            cmd = "CURR " + str(current) + ',' + strChnl            
            self.handle.write(cmd)
        except Exception:
            print('Src2722.config() sending configuration failed !')
            raise
        return True

    def readCurrent(self, channel):
        """
        Do a single current reading from specified source channel.
        Measures across a shunt resistor
        Input:   channel - 1 to 3
        Returns: float reading if OK, False if invalid channel,
                 raises exception if error
        """
        strChnl = self.checkChannel(channel)
        if not strChnl:
            return False
        try:
            cmd = 'MEAS:CURR? ' + strChnl 
            rdg = self.handle.ask(cmd)
        except Exception:
            print('Src2722.read() failed !')
            raise
        try:
            amp = float(rdg)
        except Exception:
            print('Src2722.readCurrent() conversion to float failed !')
            raise
        return amp
    
    def readVoltage(self, channel):
        """
        Do a single voltage reading from specified source channel.
        Measures across source output terminals
        Input:   channel - 1 to 3
        Returns: float reading if OK, False if invalid channel
                 raises exception if error
        """
        strChnl = self.checkChannel(channel)
        if not strChnl:
            return False
        try:
            cmd = 'MEAS:VOLT? ' + strChnl           
            rdg = self.handle.ask(cmd)
        except Exception:
            print('Src2722.readVoltage() failed !')
            raise
        try:
            volt = float(rdg)
        except Exception:
            print('Src2722.readCurrent() conversion to float failed !')
            raise
        return volt
    
    def checkChannel(self, channel):
        """
        Check if channel number is correct
        Input:      channel 1 to 3
        Returns:    channel as string if OK
                    False if invalid channel number
        """
        channel = int(channel)
        if not (1 <= channel <= 3):
            print('Src2722.checkChannel() invalid channel number !')
            return False
        return '(@' + str(channel) + ')'
    
    def startOverlapped(self, period, total):
        """ 
        !!! implementaion not finished !!!!
        Configure the DVM for reading specified samples into internal buffer
        in the background. Starts sampling under DVM timing and returns.
        Input:    period - sampling period in s
                  total - total measurement time in s
        Returns:  True if OK
                  False if failed
        """
        try:
            cmd = 'MEAS:ARR:VOLT ' + str(period) + ';'
            self.handle.write(cmd)     #sets sampling period
        except Exception:
            print('Src2722.startOverlapped() failed !')
            return False
        return True
            
    def waitOverlappedDone(self, count, timeout):
        """ 
        !!! implementaion not finished !!!!
        Wait within timeouted loop until background measurements initiated by
        startOverlapped() are finished            
        Input:    inst instrument handle
                  count number of samples to be taken
                  timeout - time within which the measurement shall be finished
        Return:   measurement results as a list
                  False if error
        """
        startTime = time.time()
        while True:         #wait until measuring flag goes to 0
            try:
                measured = self.handle.ask(":DATA:POIN?;")
                measured = measured.strip()    #remove CR            
                measured = int(measured)    #convert to number
                if measured == count:       #final number of samples achieved
                    break;
            except Exception:
                print('Src2722.waitOverlappedDone() polling failed !')
                return False
            
            if time.time() - startTime > timeout:
                print('Src2722.waitOverlappedDone() timeout !')
                return False
            
        samples = []        
        for i in range(0, count):
            try:
                reading = self.handle.ask('R? 1;')     #definite-Length block format
            except Exception: 
                print('Src2722.Reading results failed !')
                return False;
            #DLB: '#' followed by number od decimal digits to follow
            #the decimal number is length of data in bytes
            if reading[0] != '#':
                print('Src2722.DLB format error - # expected !')
                return False
            digits = int(reading[1])
            reading = reading[2 + digits:]
            samples.append(reading.strip())
    
        return samples
    
# Class self test to be run from command line
#=========================
if __name__ == '__main__':      #if run from cmd line
    print(copyr)
    #open device with given VISA name
    try:
        rm = visa.ResourceManager()     #get resource manager
    except Exception:
        print('Getting visa resource manager failed !')
        sys.exit(2)
    try:
        src = Src2722(rm, srcName)    #create device class instance
        src.open()
    except Exception:
        rm.close()
        sys.exit(2)
    
    try:
        src.configVoltSrc(1, 3., .02)   #channel 1 voltage 3V, 20mA limit
        src.enableOutput(1, True)
        rdg = src.readVoltage(1)
        print('Measured voltage = ' + str(rdg))
        
        src.setVoltage(1, 2)            #voltage to 2V
        rdg = src.readVoltage(1)
        print('Measured voltage = ' + str(rdg))

        src.configCurrSrc(1, .08, 10)  #channel 1 current 80mA, 10V limit
        rdg = src.readCurrent(1)
        print('Measured current = ' + str(rdg))

        src.setCurrent(1, .05)         #current to 50mA
        rdg = src.readCurrent(1)
        print('Measured current = ' + str(rdg))

        src.enableOutput(1, False)
    except Exception:
        raise       #let default handler to process exception
    finally:        #clean up even if exception occured
        src.close()
        rm.close()
    #gets here only if no error
    print('Done OK !')
    sys.exit(0)       #OK
    