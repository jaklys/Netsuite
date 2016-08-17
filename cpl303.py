""" 
Class for TTI PL303P programmable power supply control under VISA
and Agilent IO Library
cpl303.py (C) J.M.,rev.19-Jan-16
"""
copyr = 'cpl303.py (C) J.M.,rev.19-Jan-16'
srcName = 'ASRL4'    #default VISA name for selftest

import sys, visa, time

class Pl303:
    """
    Class implementing SCPI control of TTI PL303 power source
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
        Return: none
        """
        self.rm = rm
        self.visaName = visaName
        self.handle = None
        
    def open(self):
        """
        Connects to PL303 device with VISA name given at construction,
        Brings the device to default state, sets ASCII output format.
        Input:  none
        Output: True if OK, raises exception if failed
        """
        try:
            self.handle = self.rm.get_instrument(self.visaName)
            self.handle.write('*RST\n')   #reset device to default
            time.sleep(.5)
        except Exception:
            print('Pl303.open() failed !')
            raise
        return True

    def close(self):
        """
        Brings the device back to default state using *RST,
        closes device handle
        Input:  None
        Return: True if OK, raises exception if fails
        """
        try:
            self.handle.write('*RST\n')
            self.handle.close()
            self.handle = None
        except Exception:
            print('Pl303.close() failed !')
            raise
        return True
    
    def setVoltage(self, channel, voltage):
        """ 
        Set channel voltage to given value
        Input:  inst - instrument handle
                channel - supply channel 1 - 3
                voltage - required voltage in V
        Returns:True if OK
                raises exception if failed
        """
        try:
            cmd = 'V%d %f\n' % (channel, voltage)
            self.handle.write(cmd)    
        except Exception:
            print('Pl303.setVoltage() failed !')
            raise
        return True

    def getVoltage(self, channel):
        """ 
        Readback channel voltage 
        Input:  inst - instrument handle
                channel - supply channel 1 - 3
        Returns:float vlotage  if OK
                None or exception if failed
        """
        try:
            cmd = 'V%dO?\n' % channel
            reslt = self.handle.ask(cmd)    
        except Exception:
            print('Pl303.getVoltage() failed !')
            raise
        reslt = reslt.strip()
        if reslt[-1] != 'V':
            print('Pl303.getVoltage() unexpected reply format !')
        return float(reslt[:-1])

    def setVoltLimit(self, channel, voltage):
        """ 
        Set channel voltage limit to given value
        Input:  inst - instrument handle
                channel - supply channel 1 - 3
                voltage - required voltage in V
        Returns:True if OK
                raises exception if failed
        """
        try:
            cmd = 'OVP%d %f\n' % (channel, voltage)
            self.handle.write(cmd)    
        except Exception:
            print('Pl303.setVoltage() failed !')
            raise
        return True

    def setCurrent(self, channel, current):
        """ 
        Set channel current to given value
        Input:  inst - instrument handle
                channel - supply channel 1 - 3
                current - required current in A
        Returns:True if OK
                raises exception if failed
        """
        try:
            cmd = 'I%d %f\n' % (channel, current)
            self.handle.write(cmd)     
        except Exception:
            print('Pl303:setCurrent() !')
            raise
        return True    
        
    def getCurrent(self, channel):
        """ 
        Readback channel current
        Input:  inst - instrument handle
                channel - supply channel 1 - 3
        Returns:float current if OK
                None or exception if failed
        """
        try:
            cmd = 'I%dO?\n' % channel
            reslt = self.handle.ask(cmd)
        except Exception:
            print('Pl303:getCurrent() failed !')
            raise
        reslt = reslt.strip()   #for some reason starts with '\n'
        if reslt[-1] != 'A':
            print('Pl303.getCurrent() unexpected reply format !')
        return float(reslt[:-1])

    def setCurLimit(self, channel, current):
        """ 
        Set channel current limit to given value
        Input:  inst - instrument handle
                channel - supply channel 1 - 3
                current - required current in A
        Returns:True if OK
                raises exception if failed
        """
        try:
            cmd = 'OCP%d %f\n' % (channel, current)
            self.handle.write(cmd)     
        except Exception:
            print('Pl303:setCurrent() !')
            raise
        return True    
        
    def enableOutput(self, channel, state):
        """ 
        Switch output on/off
        Input:  inst - instrument handle
                channel - channel to be affected
                state - True means switching on
                        False switching off 
        Returns: True if OK
                 raises exception if didn't succeed
        """
        if state:
            state = 1
        else:
            state = 0
        try:
            cmd = 'OP%d %d\n' % (channel, state)
            self.handle.write(cmd)     #on/off selected channel
        except Exception:
            print('Pl303:enableOutput() selection failed !')
            raise
        return True      

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
        src = Pl303(rm, srcName)    #create device class instance
        src.open()
        src.setVoltage(1, 3.)       #channel 1 voltage to 3V
        src.setCurrent(1, .5)       #channel 1 current to 0.5A
        src.setVoltLimit(1, 10)
        src.enableOutput(1, True)  #enable channels 1 and 3
        v = src.getVoltage(1)
        print('V = %f V' % v)
        i = src.getCurrent(1)
        print('I = %f A' % i)
        time.sleep(3)

        src.enableOutput(1, False) #disable them again 
    except Exception:
        raise         #default handler will process exception  
    finally:
        src.close()   #clean up anyway to prevent memory leaks
        rm.close()

    #gets here only if no error
    print('Done OK !')
    sys.exit(0)       #OK
    