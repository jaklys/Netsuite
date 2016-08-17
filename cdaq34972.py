"""
Class for Agilent 34972A control
cdaq34972.py (C) J.M.,rev.1-Apr-16
"""
copyr = 'cdaq34972.py (C) J.M.,rev.1-Apr-16'

import sys, visa, time

class Daq34972:
    """
    Class supporting creation of any number of independent device instances
    """
    def __init__(self, rm, visaName, timeout = 5):
        """
        Constructor registers required visa name and resource manager handle
        as class attributes. Initiates device handle to None
        Input:  rm - resource manager to be stored as class attribute
                visaName - VISA address to be stored
        """
        self.rm = rm
        self.visaName = visaName
        self.handle = None
        self.timeout = timeout       #timeout value
    
    def open(self):
        """
        Connect to 34972A device with VISA name given at construction,
        bring it to default state, set ASCII output format 
        Input:  none
        Output: True if OK, raises exception if failed
        """
        try:
            self.handle = self.rm.get_instrument(self.visaName,
                                                 timeout = self.timeout)
            self.handle.write('*RST')   #reset device to default
            time.sleep(.5)
        except Exception:
            print('Exception in Daq34972.open() !')
            raise
        return True

    def close(self):
        """
        Bring the device back to default state, close handle
        Input:  None
        Returns:True if OK, raises exception if fails
        """
        if self.handle != None:
            try:
                self.handle.write('*RST')
                self.handle.close()
                self.handle = None
            except Exception:
                print('Exception in Daq34972.close() !')
                raise
        return True

    def controlSwitch(self, switch, state):
        """
        Control a mux switch
        Input:  sw - switch number
                state - True - close switch, False open switch
        Returns: True if OK, False if parameters invalid,
                 raises exception if fails
        """
        if not 101 <= switch <= 399:
            print('Daq34972.controlSwitch() illegal switch number !')
            return False
        else:
            scanList = '(@' + str(switch) + ')'
        if state:
            cmd = 'ROUT:CLOS ' + scanList          
        else:            
            cmd = 'ROUT:OPEN ' + scanList          
        try:
            self.handle.write(cmd)                #one sample per trigger
        except Exception:
            print('Exception in Daq34972.controlSwitch() !')            
            raise            
        return True
    
    def configAcFilter(self, scanList, freq):
        """
        Configure measurement speed for AC
        Input:  scanList - string describing channels to configure, format
                      '310' - single channel
                      '305:310' - range of channels
                      '202:207,209,302:308' - combination
                freq - expected min signal frequency 
                        (3 - slow, 20 - medium, 200 - fast)
        Returns: True if OK, False if parameters invalid,
                 raises exception if fails
        """
        if self.checkList(scanList) == False:
            print('Daq34972.configAcFilter() illegal scan list !')
            return False
        else:
            scanList = '(@' + scanList + ')'

        if freq < 3:
            print('Daq34972.configAcFilter() frequency too low !')
            return False
        
        #Checks OK - send setting commands
        try:
            cmd = 'SENS:VOLT:AC:BAND ' + str(freq) + ',' + scanList               
            self.handle.write(cmd)
        except Exception:
            print('Exception in Daq34972.configAcFilter() !')
            raise
        return True
        
    def configScan(self, scanList, func = 'VOLT:DC', rng = 'AUTO', nplc = 1):
        """
        Single channel configuration - sets function, range and NPLC.
        Allowed parameter values see SCPI reference manual
        Input:  scanList - string describing channels to configure, format
                      '310' - single channel
                      '305:310' - range of channels
                      '202:207,209,302:308' - combination
                func - function: 'CURR:DC, 'CURR:AC'
                                 'VOLT:DC' (default), 'VOLT:AC'   
                                 'RES', 'FRES' (2- or 4-wire)
                                 'DIG', 'TEMP'
                                 'FREQ', 'PER', 'TOT'
                rng - range as float in SI (default - 'AUTO').
                      ignored if function doesn't support ranges
                nplc - one of discrete values as string
                      ignored if function doesn't support 
        Returns: True if OK, False if parameters invalid,
                 raises exception if fails
        """
        # Check parameter consistency
        # dictionary {fnc, (min range, max range)}
        ranges = {  'CURR:DC' : (.01, 1.),
                    'CURR:AC' : (.01, 1.),
                    'DIG' : (),
                    'FREQ' : (),
                    'FRES' : (100, 1e8),
                    'PER' : (),
                    'RES' : (100, 1e8),
                    'TEMP' : (),
                    'TOT' : (),
                    'VOLT:DC' : (0.1, 300.),
                    'VOLT:AC' : (0.1, 300.)}        
        func = func.upper()
        if func in list(ranges.keys()) == False:
            print('Daq34972.configScan() - illegal function !')
            return False;
        
        noRange = ('DIG', 'FREQ', 'PER', 'TEMP', 'TOT')
        if (func in noRange) == False:   #range selection supported
            if rng == 'AUTO':
                rng = 'AUTO'   #  ':AUTO' originally
            else:
                (minR, maxR) = ranges[func]     #min and max range 
                if rng < minR or rng > maxR:
                    print('Daq34972.configScan() illegal range !')
                    return False
            strRng = ' ' + str(rng)     #convert to string
        
        hasNplc = ('VOLT:DC', 'CURR:DC', 'RES', 'FRES', 'TEMP')
        if (func in hasNplc) == True:
            if nplc < .02 or nplc > 200:
                print('Daq34972.configScan() illegal NPLC !')
                return False
        
        if self.checkList(scanList) == False:
            print('Daq34972.configScan() illegal scan list !')
            return False
        else:
            scanList = '(@' + scanList + ')'
                        
        #Checks OK - send setting commands
        try:#switch function, set range
            if (func in noRange) == False:
                cmd = 'CONF:' + func + strRng + ',' + scanList
            elif func == 'DIG':
                cmd = 'CONF:DIG:BYTE' + scanList
            else:
                cmd = 'CONF:' + func + ' DEF,' + scanList               
            self.handle.write(cmd)
            #set NPLC if supported
            if (func in hasNplc) == True:
                cmd = func + ':NPLC ' + str(nplc)            
                self.handle.write(cmd)
        except Exception:
            print('Exception in Daq34972.configScan() !')
            raise
        return True

    def readSwitch(self, switch, delay = 0):
        """
        Read one sample including closing a switch, open switch afterwards     
        Input:   switch number
        Returns: float reading if OK, False if scan list bad
                 raises exception if fails
        """
        if not 101 <= switch <= 399:
            print('Daq34972.readSwitch() illegal switch number !')
            return False
        else:
            scanList = '(@' + str(switch) + ')'
        try:
            cmd = 'ROUT:CLOS ' + scanList          
            self.handle.write(cmd)                #one sample per trigger
            if delay != 0:
                time.sleep(delay)
            reading = self.handle.ask('READ?')
            cmd = 'ROUT:OPEN ' + scanList          
            self.handle.write(cmd)                #one sample per trigger
        except Exception:
            print('Excaption in Daq34972.readSwitch() !')
            raise
        try:
            volt = float(reading)
            return volt
        except Exception:
            print('Daq34972.readSwitch() exception in conversion to float !')
            raise
        
    def read(self):
        """
        Do a single reading without toggling relays  
        Input:   None
        Returns: float reading if OK
                 raises exception if fails
        """
        try:
            reading = self.handle.ask('READ?')     
        except Exception:
            print('Exception in Daq34972.read() !')
            raise
        try:
            volt = float(reading)
            return volt
        except Exception:
            print('Daq34972.read() exception in conversion to float !')
            raise
    
    def startOverlapped(self, period, total):
        """ 
        Configure the DVM for reading specified samples into internal buffer
        in the background. Starts sampling under DVM timing and returns.
        Input:    period - sampling period in s
                  total - total measurement time in s
        Returns:  True if OK
                  raises exception if failed
        """
        try:
            self.handle.write(':TRIG:SOUR BUS;')  #triggered by command
            cmd = ':SAMP:COUN ' + str(total/period) + ';'
            self.handle.write(cmd)     #sets number of samples per trigger
            self.handle.write(':SAMP:SOUR TIM;')  #sampled by timer
            cmd = ':SAMP:TIM ' + str(period) + ';'
            self.handle.write(cmd)     #sets sampling period
            self.handle.write(':INIT:IMM;') #DVM to "wait for trigger" 
            self.handle.write('*TRG;')
        except Exception:
            print('Exception in Daq34972.startOverlapped() !')
            raise
        return True
            
    def waitOverlappedDone(self, count, timeout):
        """ 
        Wait within timeouted loop until background measurements initiated by
        startOverlapped() are finished            
        Input:    inst instrument handle
                  count number of samples to be taken
                  timeout - time within which the measurement shall be finished
        Return:   measurement results as a list of float
                  False if timeout or readi data format error
                  raises exception if fails
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
                print('Exception in Daq34972.waitOverlappedDone() polling !')
                raise
            
            if time.time() - startTime > timeout:
                print('Daq34972.waitOverlappedDone() timeout !')
                return False
            
        samples = []        
        for i in range(0, count):
            try:
                reading = self.handle.ask('R? 1;')     #definite-Length block format
            except Exception: 
                print('Daq34972.Reading results failed !')
                raise;
            #DLB: '#' followed by number od decimal digits to follow
            #the decimal number is length of data in bytes
            if reading[0] != '#':
                print('Daq34972.DLB format error - # expected !')
                return False
            digits = int(reading[1])
            reading = reading[2 + digits:]
            reading = reading.strip()
            try:
                rdg = float(reading)
            except Exception:
                print('Daq34972.waitOverlappedDone() Exception in conversion to float !')
                raise
            samples.append(rdg)
    
        return samples
    
    def setTimeout(self, timeout):
        """
        Change timeout for waiting for DVM measurement
        Input:      timeout - seconds, 5s default
        Returns:    None
        """
        self.timeout = timeout
    
    def checkList(self, chlist):
        """
        Check channel list creation rules.
        Input:  list - channel list as a string without leading
                    '(@' and final ')'
        Returns: True if OK, False if scan list syntax error
        """
        items = chlist.split(',')       #items single switches or ranges
        for item in items:
            item = item.strip()                #remove whitespace
            if item.find(':') != -1:    #range
                (fromCh, toCh) = item.split(':')
                fromCh = int(fromCh)
                toCh = int(toCh)
                if fromCh > toCh:
                    print('Daq34972:checkList() invalid range !')
                    return False
                if not (101 <= fromCh <= 399 and 101 <= toCh <= 399):
                    print('Daq34972:checkList() invalid channel number !')
                    return False
            else:
                chan = int(item)
                if not (101 <= chan <= 440):
                    print('Daq34972:checkList() invalid channel number !')
                    return False
        return True
    
# Selftest
#==================================================================
if __name__ == '__main__':      #self test   

#    visaName = '34972LAN'     #default VISA name for selftest - LAN
    visaName = '34972A'     #default VISA name for selftest - USB

    print(copyr) 
    """
    # checkList() test
    dvm = Daq34972('a', visaName)    #create device class instance
    pattern = '101 , 201:205, 301: 306, 405'
    reslt = dvm.checkList(pattern)  #call function to debug
    print(reslt)
    sys.exit(0)
    """
    #open device with given VISA name
    try:
        rm = visa.ResourceManager()     #get resource manager
    except Exception:
        print('Getting visa resource manager failed !')
        sys.exit(2)
    try:
        dvm = Daq34972(rm, visaName)    #create device class instance
        dvm.open()
    except Exception:
        rm.close()
        sys.exit(2)
        
    reslt = False
    try:
        dvm.controlSwitch(101, True)
        time.sleep(.1)        
        dvm.controlSwitch(101, False)
        time.sleep(.1)        

        if dvm.configScan('101', 'volt:dc', 10, 1):  #fnc, channel, rng, NPLC
            v = dvm.read()
            if v != False:
                print('Measured ' + str(v))
            reslt = True
        else:
            print('Configuration failed !') 
    except Exception:
        raise       #leave default handler to process exception
    finally:        #clean up in any case to prevent memory leaks
        try:
            dvm.close()     
            rm.close()
        except Exception:
            reslt = False
    if reslt:
        print('Done OK !')
        sys.exit(0)       #OK
    else:
        print('Done with error !')
        sys.exit(2)           #error
    
