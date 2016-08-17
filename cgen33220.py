""" 
Class for Agilent 33220A Function generator control under VISA
and Agilent IO Library
cgen33220.py (C) J.M.,rev.15-Jan-16
"""
copyr = 'cgen33220.py (C) J.M.,rev.15-Jan-16'
genName = '33220A'    #default VISA name for self test

import sys, time
import visa
# import visasim as visa     #simulator 

class Gen33220:
    functions = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
    
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
        self.maxV = 10          #max voltage for high impedance load
        self.function = 'SIN'   #default function
        
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
            print('Gen33220.open() failed !')
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
                print('Gen33220.close() failed !')
                raise
        return True
    
    def setVoltage(self, ppAmp, offs):
        """ 
        Set output pp voltage and DC offset to given values.
        Input:  inst - instrument handle
                ppAmp - required pp amplitude in V
                offs - offset in V
        Returns:True if OK, False if invalid,
                raises exception if failed
        """
        if ppAmp < .01 or ppAmp > self.maxV:
            print('Gen33220.setVoltage() pp amplitude out of range !')
            return False
        if abs(offs) > self.maxV - ppAmp/2:
            print('Gen33220.setVoltage() DC offset out of range !')
            return False
            
        try:
            cmd = 'VOLT ' + str(ppAmp)
            self.handle.write(cmd)     #sets sampling period
            
            cmd = 'VOLT:OFFSET ' + str(offs)
            self.handle.write(cmd)     #sets sampling period
        except Exception:
            print('Gen33220.setVoltage() failed !')
            raise
        return True

    def setFrequency(self, freq):
        """ 
        Set channel current to given value. Keeps actual channel configuration.
        Input:  inst - instrument handle
                freq - required frequency in Hz
        Returns:True if OK, False if invalid,
                raises exception if failed
        """
        fOk = True
        if self.function == 'SIN' or self.function == 'SQU':
            if freq < 1e-6 or freq > 20E6:
                fOk = False
        elif self.function == 'RAMP':
            if freq < 1E-6 or freq > 2e5:
                fOk = False
        elif self.function == 'PULS':
            if freq < 5E-4 or freq > 5E6:
                fOk = False
        elif self.function == 'USER':  
            if freq < 1E-6 or freq > 6E6:
                fOk = False
            
        if not fOk:
            print('Gen33220.setFrequency() failed !')
            return False
        
        try:
            cmd = 'FREQ ' + str(freq)
            self.handle.write(cmd)     #sets frequency
        except Exception:
            print('Gen33220.setFrequency() failed !')
            raise
        return True    
        
    def enableOutput(self, state):
        """ 
        Switch source output on
        Input:   state - True on, False - off
        Returns: True if OK, False if invalid channel,
                 raises exceptionif didn't succeed
        """
        if state:
            cmd = 'OUTP ON, '
        else:
            cmd = 'OUTP OFF, '
        try:
            self.handle.write(cmd)
        except Exception:
            print('Gen33220.enableOutput() set state failed !')        
            raise    
        return True      

    def selectFunction(self, function):
        """
        Issue FUNC command
        Input:  function - string describing the mode
        Returns:True if OK, False if invalid channe or current range,
                raises exception if failed
        """
        function = function.upper()
        if function in self.functions:
            self.function = function        #memorize it
            cmd = 'FUNC ' + function 
            try:
                self.handle.write(cmd)
            except Exception:
                print('Gen33220.selectFunction() function selection failed !')
                raise
        else:   # range exceeds maximum available
            print('Gen33220.selectFunction() invalid function required !')
            return False
        return True

    def readFunction(self):
        """
        Returns string describing chosen function
        Input:   none
        Returns: string reading if OK
                 raises exception if error
        """
        try:
            cmd = 'FUNC?'
            rdg = self.handle.ask(cmd)
        except Exception:
            print('Gen33220.readFunction() failed !')
            raise
        rdg = rdg.strip()
        return rdg
    
# Class self test to be run from command line
#============================================
if __name__ == '__main__':      #if run from cmd line
    print(copyr)
    #open device with given VISA name
    try:
        rm = visa.ResourceManager()     #get resource manager
    except Exception:
        print('Getting visa resource manager failed !')
        sys.exit(2)
    try:
        gen = Gen33220(rm, genName)    #create device class instance
        gen.open()
    except Exception:
        rm.close()
        sys.exit(2)
    
    try:
        res = gen.selectFunction('SIN')
        res = gen.setFrequency(300.)     #300Hz
        res = gen.setVoltage(1, 0)      #1Vpp, no offset
        res = gen.enableOutput(True) #enable output
        res = gen.readFunction()
    except Exception:
        raise       #let default handler to process exception
    finally:        #clean up even if exception occured
        gen.close()
        rm.close()
    #gets here only if no error
    print('Done OK !')
    sys.exit(0)       #OK
    