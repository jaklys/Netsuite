""" 
Class for Hameg HMP4030 programmable power supply control under VISA
and Agilent IO Library
csrcHmp4030.py (C) J.M.,rev.13-Jan-1
"""
copyr = 'csrcHmp4030.py (C) J.M.,rev.13-Jan-16'
srcName = 'HMP4030'    #default VISA name for selftest

import sys, visa, time

class Hmp4030:
    """
    Class implementing SCPI control of Hameg HMP4030 power source
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
        Connects to HMP4030 device with VISA name given at construction,
        Brings the device to default state, sets ASCII output format.
        Input:  none
        Output: True if OK, raises exception if failed
        """
        try:
            self.handle = self.rm.get_instrument(self.visaName)
            self.handle.write('*RST')   #reset device to default
            time.sleep(.5)
        except Exception:
            print('Hmp4030.open() failed !')
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
            self.handle.write('*RST')
            self.handle.close()
            self.handle = None
        except Exception:
            print('Hmp4030.close() failed !')
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
            cmd = 'OUT%d' % channel
            cmd = 'INST ' + cmd + ';'
            self.handle.write(cmd)     #selects source channel
            cmd = 'VOLT %f;' % voltage
            self.handle.write(cmd)     
        except Exception:
            print('HMP4030.setVoltage() failed !')
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
            cmd = 'OUT%d' % (channel)
            cmd = 'INST ' + cmd + ';'
            self.handle.write(cmd)     #selects source channel
            time.sleep(.1)
            cmd = 'CURR %f;' % (current)
            time.sleep(.1)
            self.handle.write(cmd)    
        except Exception:
            print('HMP4030:setCurrent() !')
            raise
        return True    
        
    def enableOutputs(self, mask, state):
        """ 
        Switch outputs on/off
        Input:  inst - instrument handle
                mask - channels to be affected selected by a mask:
                    bit0 - channel1,
                    bit1 - channel2,
                    bit2 - channel3
                state - True means switching on
                        False switching off 
        Returns: True if OK
                 raises exception if didn't succeed
        """
        try:
            for i in range(0, 3):
                cmd = 'INST '
                cmd = cmd + ('OUT%d;' % (i + 1))
                self.handle.write(cmd)     #selects sequentially all channels
                time.sleep(0.1)
                cmd = 'OUTP:SEL '    
                if (mask & 1<<i) != 0:
                    cmd = cmd + '1;'        #activate
                else:
                    cmd = cmd + '0;'        #deactivate
                self.handle.write(cmd)     #on/off selected channel
        except Exception:
            print('HMP4030:setOutput() selection failed !')
            raise
        
        cmd = 'OUTP:GEN '
        if state == True:
            cmd = cmd + 'ON;'
        else:
            cmd = cmd + 'OFF;'
        try:
            self.handle.write(cmd)
        except Exception:
            print('HMP4030.setOutput() set state failed !')        
            raise    
        return True

    def sendCommand(self, cmd):
        """
        Send command to the source
        Input: cmd - SCPI string
        """
        try:
            self.handle.write(cmd)
        except Exception:
            print('HMP4030:sendCommand() failed !')
            raise

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
        src = Hmp4030(rm, srcName)    #create device class instance
        src.open()
    finally:
        rm.close()
        raise
    
    try:
        src.setVoltage(1, 3.)       #channel 1 voltage to 3V
        src.setCurrent(1, .5)       #channel 1 current to 0.5A
        src.enableOutputs(5, True)  #enable channels 1 and 3
                    
        time.sleep(3)

        src.enableOutputs(5, False) #disable them again 
    except Exception:
        raise         #default handler will process exception  
    finally:
        src.close()   #clean up anyway to prevent memory leaks
        rm.close()

    #gets here only if no error
    print('Done OK !')
    sys.exit(0)       #OK
    