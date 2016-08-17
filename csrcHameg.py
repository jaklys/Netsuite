""" 
Class for Hameg HMP4030, HMP2030 programmable power supply control under VISA
and Agilent IO Library and LAN or USB interface
All commands terminated by '\n' else virtual COM doesn't work
csrcHameg.py (C) J.M.,rev.16-Oct-15
"""
copyr = 'csrcHameg.py (C) J.M.,rev.16-Oct-15'
#srcName = 'HMP2030'      #VISA alias for USB
srcName = 'ASRL10'      #VISA name for USB
#srcName = 'HMP4030'     #VISA name for LAN

import sys, visa, time

class SrcHameg:
    """
    Class implementing SCPI control of Hameg HMP4030 power source
    control via Agilent IO Libraries and VISA interface
    """
    def __init__(self, rm, visaName, nrOfChannels = 3):
        """
        Constructor registers the visa name and resource manager handle
        as class attributes. Resource manager handle has to be fetched
        before class instance created.
        Initiates the device handle to None
        Input:  rm - resource manager to be stored as class attribute
                visaName - VISA address to be stored
                nrOfChannels - available channels, default 3
        Return: none
        """
        self.rm = rm
        self.visaName = visaName
        self.handle = None
        self.channels = nrOfChannels
        self.opened = False
        
    def open(self):
        """
        Connects to Hameg device with VISA name given at construction,
        Brings the device to default state, sets ASCII output format.
        Input:  none
        Output: True if OK, raises exception if failed
        """
        try:
            self.handle = self.rm.get_instrument(self.visaName)
            self.handle.term_chars = '\n'
            self.handle.write('*RST')   #reset device to default
            time.sleep(.5)
        except Exception:
            print('SrcHameg.open() failed !')
            raise
        print("%s opened !" % self.visaName)
        self.opened = True
        return True

    def close(self):
        """
        Brings the device back to default state using *RST,
        closes device handle
        Input:  None
        Return: True if OK, raises exception if fails
        """
        if self.opened:
            try:
                self.handle.write('*RST')
                self.handle.close()
                self.handle = None
            except Exception:
                print('SrcHameg.close() failed !')
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
        if channel > self.channels:
            print('SrcHameg.setVoltage() - illegal channel !')
            raise
        try:
            cmd = 'INST OUTP%d' % channel
            self.handle.write(cmd)     #selects source channel
            time.sleep(0.1)
            
            cmd = 'VOLT %.3f' % voltage
            self.handle.write(cmd)     
            time.sleep(0.1)
        except Exception:
            print('SrcHameg.setVoltage() failed !')
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
        if channel > self.channels:
            print('SrcHameg.setCurrent() - illegal channel !')
            raise
        try:
            cmd = 'OUTP%d' % (channel)
            cmd = 'INST ' + cmd + ';'
            self.handle.write(cmd)     #selects source channel
            time.sleep(.1)
            
            cmd = 'CURR %.3f' % (current)
            self.handle.write(cmd)    
            time.sleep(.1)
        except Exception:
            print('SrcHameg.setCurrent() !')
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
            bit = 1
            for i in range(1, self.channels + 1):
                cmd = 'INST OUTP%d' % i
                self.handle.write(cmd)     
                time.sleep(0.1)
                if (mask & bit != 0):
                    cmd = 'OUTP:SEL 1'
                else:
                    cmd = 'OUTP:SEL 0'
                self.handle.write(cmd)
                time.sleep(0.1)
                bit *= 2
            cmd = 'OUTP:GEN '
            if state == True:
                cmd = cmd + '1'
            else:
                cmd = cmd + '0'
            self.handle.write(cmd)
            time.sleep(0.1)
        except Exception:
            print('SrcHameg.setOutput() failed !')        
            raise    
        return True

    def configVoltSrc(self, channel, volt, currLimit):
        """
        Configure channel as voltage source with given current limit.
        Input:  channel - 1 to 3
                volt - float, voltage in V
                currLimit - float, maximum provided current
        Returns:True if OK, False if invalid channe or current range,
                raises exception if failed
        """
        if channel > self.channels:
            print('SrcHameg.configVoltSrc() - illegal channel !')
            raise

        try:
            cmd = "INST OUTP%d" % channel   #select channel
            self.handle.write(cmd)
            time.sleep(0.1)
            
            cmd = "VOLT:PROT %f" % volt
            self.handle.write(cmd)
            time.sleep(0.1)

            cmd = "CURR %f" % currLimit
            self.handle.write(cmd)
            time.sleep(0.1)
        except Exception:
            print('SrcHameg.configVoltSrc() sending configuration failed !')
            raise
        return True

    def configCurrSrc(self, channel, current, voltLimit):
        """
        Configure channel as voltage source, set overvoltage protection
        Input:  channel - 1 to 3
                current - float, voltage in A
                voltLimit - float, overvoltage protection
        Returns:True if OK, False if invalid channel or current range
                raises exception if failed
        """
        if channel > self.channels:
            print('SrcHameg.configCurrSrc() - illegal channel !')
            raise

        try:
            cmd = "INST OUTP%d" % channel   #select channel
            self.handle.write(cmd)
            time.sleep(0.1)

            cmd = "VOLT:PROT %f" % voltLimit
            self.handle.write(cmd)
            time.sleep(0.1)

            cmd = "CURR %f" + current            
            self.handle.write(cmd)
            time.sleep(0.1)

        except Exception:
            print('SrcHameg.configCurrSrc() sending configuration failed !')
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
        if channel > self.channels:
            print('SrcHameg.configCurrSrc() - illegal channel !')
            raise

        try:
            cmd = "INST OUTP%d" % channel   #select channel
            self.handle.write(cmd)
            time.sleep(0.1)

            cmd = 'MEAS:CURR?' 
            rdg = self.handle.ask(cmd)
        except Exception:
            print('SrcHameg.readCurrent() failed !')
            raise
        try:
            amp = float(rdg)
        except Exception:
            print('SrcHAmeg.readCurrent() conversion to float failed !')
            raise
        return amp
    
    def readVoltage(self, channel):
        """
        Do a single voltage reading from specified source channel.
        Measures across source output terminals
        Input:   channel - 1 to 3
        Returns: float reading if OK
                 raises exception if error
        """
        if channel > self.channels:
            print('SrcHameg.configCurrSrc() - illegal channel !')
            raise

        try:
            cmd = 'INST OUTP%d' % channel   #select channel
            self.handle.write(cmd)
            time.sleep(0.1)

            cmd = 'MEAS:VOLT?'           
            rdg = self.handle.ask(cmd)
        except Exception:
            print('SrcHameg.readVoltage() failed !')
            raise
        try:
            volt = float(rdg)
        except Exception:
            print('SrcHameg.readVoltage() conversion to float failed !')
            raise
        return volt
    
    def sendCommand(self, cmd):
        """
        Send command to the source
        Input: cmd - SCPI string
        """
        try:
            self.handle.write(cmd + '\n')
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
        src = SrcHameg(rm, srcName)    #create device class instance
        src.open()
    except:
        raise
    
    try:
        src.setVoltage(1, 3.)       #channel 1 voltage to 3V
        src.setCurrent(1, .5)       #channel 1 current to 0.5A

        src.setVoltage(2, 6.)       #channel 2 voltage to 6V
        src.setCurrent(2, .4)       #channel 2 current to 0.4A

        src.setVoltage(3, 9.)       #channel 3 voltage to 9V
        src.setCurrent(3, .3)       #channel 3 current to 0.3A

        src.enableOutputs(5, True)  #enable channels 1 and 3
                    
        time.sleep(1)
        volt = src.readVoltage(1)
        curr = src.readCurrent(1)
        resl = 'V=%f, I=%f' % (volt, curr)
        print(resl)
        
        src.enableOutputs(5, False) #disable them again 
    except Exception:
        raise         #default handler will process exception  
    finally:
        src.close()   #clean up anyway to prevent memory leaks
        rm.close()

    #gets here only if no error
    print('Done OK !')
    sys.exit(0)       #OK
    