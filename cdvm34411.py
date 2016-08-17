"""
Class for Agilent 34411A DVM control
cdvm34411.py (C) J.M.,rev.30-Jan-16
"""
copyr = 'cdvm34411.py (C) J.M.,rev.30-Jan-16'
visaName = '34411A'     #default VISA name for selftest

import sys, visa, time

class Dvm34411:
    """
    Class supporting creation of any number of independent device instances
    """
    def __init__(self, rm, visaName):
        """
        Constructor registers required visa name and resource manager handle
        as class attributes. Initiates device handle to None
        Input:  rm - resource manager to be stored as class attribute
                visaName - VISA address to be stored
        """
        self.rm = rm
        self.visaName = visaName
        self.handle = None
        self.timeout = 5       #default timeout value
    
    def open(self):
        """
        Connect to 34411A device with VISA name given at construction,
        bring it to default state, set ASCII output format 
        Input:  none
        Returns: True if OK, exception raised if failed
        """
        try:
            self.handle = self.rm.get_instrument(self.visaName)
            self.handle.write('*RST')   #reset device to default
            time.sleep(.5)
            self.handle.write(':FORM:DATA ASC')   #return ASCII
        except Exception:
            print('Dvm34411.open() failed !')
            raise
        return True

    def close(self):
        """
        Bring the device back to default state, close handle
        Input:  None
        Returns:True if OK, exception raised if failure
        """
        try:
            self.handle.write('*RST')
            self.handle.close()
            self.handle = None
        except Exception:
            print('Dvm34411.close() failed !')
            raise
        return True

    def config(self, func = 'VOLT:DC', rng = 'AUTO', nplc = 1, aZero = True):
        """
        DVM configuration - sets function, range and NPLC.
        Allowed parameter values see SCPI reference manual
        Input:  func - function: 'VOLT:DC' (default), 'VOLT:AC'   
                                 'CURR:DC, 'CURR:AC', 'CAP', 'TEMP',
                                 'CON', 'DIOD', 'FREQ',
                                 'RES', 'FRES' (2- or 4-wire)
                rng - range as float in SI (default - 'AUTO').
                      ignored if function doesn't support ranges
                nplc - one of discrete values as string
                      ignored if function doesn't support  
                aZero - True or False - set auto-zero function
                      ignored if function doesn't support
        Returns: True if OK, False if parameter invalid,
                raises exception if fails
        """
        # Check parameter consistency
        # dictionary {fnc, (min range, max range)}
        ranges = {'CAP' : (1e-9, 1e-5), 
                'CURR:DC' : (1e-5, 3.),
                'CURR:AC' : (1e-5, 3.),
                'FRES' : (100, 1e9),
                'RES' : (100, 1e9),
                'VOLT:DC' : (0.1, 1000.),
                'VOLT:AC' : (0.1, 750.),
                'FREQ' : (),    
                'PER' : (),
                'CON' : (),     #functions with no range support
                'DIOD' : (),
                'TEMP' : ()}        
        func = func.upper()
        if func in list(ranges.keys()) == False:
            print('Dvm34411.config() - illegal function !')
            return False;
        
        noRange = ('CON', 'DIOD', 'FREQ', 'PER', 'TEMP')
        if (func in noRange) == False:   #range selection supported
            if rng == 'AUTO':
                rng = ':AUTO'
            else:
                (minR, maxR) = ranges[func]     #min and max range 
                if rng < minR or rng > maxR:
                    print('Dvm34411.config() illegal range !')
                    return False
            rng = ' ' + str(rng)     #convert to string
        
        hasNplc = ('VOLT:DC', 'CURR:DC', 'RES', 'FRES', 'TEMP')
        if (func in hasNplc) == True:
            if nplc < .001 or nplc > 100:
                print('Dvm34411:config() illegal NPLC !')
                return False
        
        #Checks OK - send setting commands
        try:#switch function
            cmd = 'FUNC:ON "' + func + '"'
            self.handle.write(cmd)
            time.sleep(.2)
            #set range if supported
            if (func in noRange) == False:
                cmd = func + ':RANGE' + rng            
                self.handle.write(cmd)
                time.sleep(.2)
            #set NPLC if supported
            if (func in hasNplc) == True:
                cmd = func + ':NPLC ' + str(nplc)            
                self.handle.write(cmd)
            #set autozero if supported
            if (func in ('VOLT:DC', 'CURR:DC', 'RES', 'TEMP')) == True:
                cmd = func + ':ZERO:AUTO '
                if aZero: cmd += '1'
                else: cmd += '0'
                self.handle.write(cmd)
        except Exception:
            print('Dvm34411.config() sending configuration failed !')
            raise
        return True

    def read(self):
        """
        Do a single reading.
        Input:   None
        Returns: float measured value if OK,
                 False if timeout or returned data format bad,
                 raises exception if fails
        """
        try:
            cmd = 'SAMP:COUN 1'          
            self.handle.write(cmd)                #one sample per trigger
            self.handle.write('TRIG:SOUR BUS')  #triggered by command
            self.handle.write('TRIG:COUN 1')    #one trigger to return to wait for trg
            self.handle.write('INIT:IMM')       #DVM to "wait for trigger" 
            self.handle.write('*TRG')
            startTime = time.time()
            while True:                     #wait until measuring flag goes to 0
                try:
                    measured = self.handle.ask("DATA:POIN?")
                    measured = measured.strip()    #remove CR            
                    measured = int(measured)    #convert to number
                    if measured == 1:       #final number of samples achieved
                        break;
                except Exception:
                    print('Dvm34411:read() polling failed !')
                    raise
                
                if time.time() - startTime > self.timeout:
                    print('Dvm34411:read() timeout !')
                    return False
                
            time.sleep(1)  
            reading = self.handle.ask('R? 1;')     #definite-Length block format
        except Exception:
            print('Dvm34411.read() failed !')
            raise
        if reading[0] != '#':
            print('Dvm34411.read() DLB format error - # expected !')
            return False
        digits = int(reading[1])
        reading = reading[2 + digits:]
        rdg = float(reading)
        return rdg
    
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
            print('Dvm34411.startOverlapped() failed !')
            raise
        return True
            
    def waitOverlappedDone(self, count, timeout):
        """ 
        Wait within timeouted loop until background measurements initiated by
        startOverlapped() are finished            
        Input:    inst instrument handle
                  count number of samples to be taken
                  timeout - time within which the measurement shall be finished
        Return:   measurement results as a list of float if OK
                  False if timeout or data format error 
                  rases exception if fails
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
                print('Dvm34411.waitOverlappedDone() polling failed !')
                raise
            
            if time.time() - startTime > timeout:
                print('Dvm34411.waitOverlappedDone() timeout !')
                return False
            
        samples = []        
        for i in range(0, count):
            try:
                reading = self.handle.ask('R? 1;')     #definite-Length block format
            except Exception: 
                print('Dvm34411.Reading results failed !')
                raise;
            #DLB: '#' followed by number od decimal digits to follow
            #the decimal number is length of data in bytes
            if reading[0] != '#':
                print('Dvm34411.DLB format error - # expected !')
                return False
            digits = int(reading[1])
            reading = reading[2 + digits:]
            samples.append(reading.strip())
    
        return samples
    
    def setTimeout(self, timeout):
        """
        Change timeout for waiting for DVM measurement
        Input:      timeout - seconds, 5s default
        Returns:    None
        """
        self.timeout = timeout
    
# Selftest
#==================================================================
if __name__ == '__main__':      #self test   
    print(copyr)    
    try:
        rm = visa.ResourceManager()     #get resource manager
    except Exception:
        print('Getting visa resource manager failed !')
        sys.exit(2)
    try:
        dvm = Dvm34411(rm, visaName)    #create device class instance
        dvm.open()
    except Exception:
        rm.close()      #close resource manager to prevent memory leaks
        sys.exit(2)
        
    reslt = False
    try:
        if dvm.config('volt:dc', 10, 1, True):      #fnc, rng, NPLC, autoZ
            v = dvm.read()
            if v != False:
                print('Measured ' + str(v))
        reslt = True
    except Exception:
        raise       #leave default handler to describe error
    finally:        #clean up in any case to keep IO Lib healthy
        dvm.close()
        rm.close()
    if reslt:
        print('Done OK !')
        sys.exit(0)
    else:
        print('Done with error !')
        sys.exit(2)
    
        
    
