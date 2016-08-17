"""
Class for Keithley 3706 controled by Visa,
Keithley 3706A Six-Slot System Switch
Mainframe with High Performance Digital Multimeter
cdaq3706.py (C) J.M.,rev.22-Jan-16
"""

copyr = 'cdaq3706.py (C) J.M.,rev.22-Jan-16'

import sys, visa, time

class Daq3706:
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
        self.opened = False
        self.slots = []              #no slot detected
        
    def open(self):
        """
        Connect to the device with VISA name given at construction,
        bring it to default state, set ASCII output format 
        Input:  none
        Output: True if OK, raises exception if failed
        """
        if self.opened:                 #already opened
            return True        
        try:
            self.handle = self.rm.get_instrument(self.visaName,
                                                 timeout = self.timeout)
            self.handle.write('*RST')   #reset device to default
            time.sleep(.5)
            cmd = 'beeper.enable = beeper.ON'    
            self.handle.write(cmd)
            cmd = 'beeper.beep(.1, 4800)'    
            self.handle.write(cmd)
        except Exception:
            print('Exception in Daq3706.open() !')
            raise
        self.opened = True
        print('K3706 opened !')
        return True

    def scanSlots(self):
        """
        Reads IDs of cards inserted into slots and stores to a list
        of their types
        Input:  None
        Return: True if OK
                False if failed to detect any card
                exception if error
        """
        self.slots = []
        anySlot = False
        for i in range(1, 7):       #check which cards are present in slots
            try:
                cmd = 'print(slot[%d].idn)' % i
                idn = self.handle.ask(cmd)
                items = idn.split(',')        #separate items
                if items[0] == 'Pseudo':
                    slotType = items[1]
                else:
                    slotType = items[0]
                slotType = slotType.strip()
                self.slots.append(slotType)   #only type number
                if slotType != 'Empty Slot':
                    anySlot = True
            except:
                raise
        if not anySlot:
            print('No card detected in slots !')
            return False
        return True
    
    def close(self):
        """
        Bring the device back to default state, close handle
        Input:  None
        Returns:True if OK, raises exception if fails
        """
        if self.opened:
            try:
                self.handle.write('*RST')
                self.handle.close()
                self.handle = None
            except Exception:
                print('Exception in Daq3706.close() !')
                raise
            self.opened = False
        return True

    def controlSwitch(self, switch, state):
        """
        Control a mux switch
        Input:  sw - switch number
                state - True - close switch, False open switch
        Returns: True if OK, False if parameters invalid,
                 raises exception if fails
        """
        if not self.checkSwitchNumber(switch):
            print('Daq3706.controlSwitch() illegal switch number !')
            return False
        else:
            scanList = "'" + str(switch)
        if state:
            cmd = 'channel.close("' + str(switch) + '")'
        else:            
            cmd = 'channel.open("' + str(switch) + '")'
        try:
            self.handle.write(cmd)                #one sample per trigger
        except Exception:
            print('Exception in Daq3706.controlSwitch() !')            
            raise            
        return True
    
    def configAcFilter(self, scanList, freq):
        """
        Configure measurement speed for AC - not fixed for Keithley !!!
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
            print('Daq3706.configAcFilter() illegal scan list !')
            return False
        else:
            scanList = '(@' + scanList + ')'

        if freq < 3:
            print('Daq3706.configAcFilter() frequency too low !')
            return False
        
        #Checks OK - send setting commands
        try:
            cmd = 'SENS:VOLT:AC:BAND ' + str(freq) + ',' + scanList               
            self.handle.write(cmd)
        except Exception:
            print('Exception in Daq3706.configAcFilter() !')
            raise
        return True
        
    def configDmm(self, func = 'dcvolt', rng = 'auto', nplc = 1):
        """
        Configuration of the DMM - sets function, range and NPLC.
        Allowed parameter values see reference manual
        Input:  func - function: 'accurrent', 'acvolts', 'commonsideohms',
                                 'dcvolts' (default), 'fourwireohms',
                                 'frequency', 'period', 'temperature',
                                 'twowireohms'
                rng - range as float in SI (default 'auto').
                      ignored if function doesn't support ranges
                nplc - float, ignored if function doesn't support 
        Returns: True if OK, False if parameters invalid,
                 raises exception if fails
        """
        # Check parameter consistency
        # dictionary {fnc, (min range, max range)}
        ranges = {  'accurrent' : (0, 3.1),
                    'acvolts' : (0, 303.),
                    'commonsideohms' : (0, 120E6),
                    'dccurrent' : (0, 3.1),
                    'dcvolts' : (0, 303.),
                    'fourwireohms' : (0, 120e6),
                    'frequency' : (),
                    'period' : (),
                    'temperature' : (),
                    'twowireohms' : (0, 120e6)}
        func = func.lower()
        if func in list(ranges.keys()) == False:
            print('Daq3706.configDmm() - illegal function !')
            return False;
        
        noRange = ('period', 'temperature', 'frequency')
        if(func in noRange) == False:   #range selection supported
            if rng == 'auto':
                rng = 'auto'   
            else:
                (minR, maxR) = ranges[func]     #min and max range 
                if rng < minR or rng > maxR:
                    print('Daq3706.configDmm() illegal range !')
                    return False
        else:
            rng = None
        
        noNplc = ('frequency', 'period')
        if (func in noNplc) == False:
            if nplc < .2 or nplc > 200:
                print('Daq3706.configDmm() illegal NPLC !')
                return False
        else:
            nplc = None
        
        #Checks OK - send setting commands
        try:#switch function, set range
            cmd = 'dmm.func="' + func + '"'
            self.handle.write(cmd)
            
            if rng != None:
                cmd = 'dmm.range=' + str(rng)
                self.handle.write(cmd)

            if nplc != None:
                cmd = 'dmm.nplc=' + str(nplc)
                self.handle.write(cmd)
        except Exception:
            print('Exception in Daq3706.configDmm() !')
            raise
        return True

    def readSwitch(self, switch, delay = 0):
        """
        Read one sample including closing a switch, open switch afterwards     
        Input:   switch number
        Returns: float reading if OK, False if scan list bad
                 raises exception if fails
        """
        if not self.checkSwitchNumber(switch):
            print('Daq3706.readSwitch() illegal switch number !')
            return False
        try:
            cmd = 'channel.close("' + str(switch) + '")'
            self.handle.write(cmd)                #one sample per trigger
            if delay != 0:
                time.sleep(delay)
            
            reading = self.read()                 #perform reading

            cmd = 'channel.open("' + str(switch) + '")'
            self.handle.write(cmd)                #one sample per trigger
        except Exception:
            print('Exception in Daq3706.readSwitch() !')
            raise
        return reading
        
    def read(self):
        """
        Do a single reading without toggling relays  
        Input:   None
        Returns: float reading if OK
                 raises exception if fails
        """
        try:
            cmd = 'buffer = dmm.makebuffer(1)'
            self.handle.write(cmd)
            
            cmd = 'dmm.measurecount = 1'
            self.handle.write(cmd)
    
            cmd = 'print(dmm.measure(buffer))'
            reslt = self.handle.ask(cmd)
        except:
            print('Daq3706.read() failed !')
            raise
        try:
            cmd = 'buffer=nil'          #delete buffer
            self.handle.write(cmd)
            reading = float(reslt)
        except:
            print('Daq3706.read() reading conversion to float failed !')
            return False
        return reading

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
                    '(' and final ')'
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
                    print('Daq3706.checkList() invalid range !')
                    return False
                if (not self.checkSwitchNumber(fromCh) or
                    not self.checkSwitchNumber(toCh)):
                    print('Daq3706.checkList() invalid channel number !')
                    return False
            else:
                chan = int(item)
                if not self.chsckSwitchNumber(chan):
                    print('Daq3706.checkList() invalid channel number !')
                    return False
        return True
    
    def checkSwitchNumber(self, switch):
        """
        Check if switch really exists.
        Input:  switch - switch number: first digit - slot number,
                         the rest switch number
        Returns: True if OK, False if switch doesn't exist
        """
        if len(self.slots) != 6:
            print('Daq3706.checkSwitchNumber() - No cards in slots detected !')
            return False
        string = '%d' % switch
        slot = int(string[0])
        switch = int(string[1:])
        if slot == 0 or slot > 6:
            print('Daq3706.checkSwitchNumber() - Invalid slot number !')
            return False
        if self.slots[slot - 1] == 'Empty Slot':   #starts from 0
            print('Daq3706.checkSwitchNumber() - Empty slot addressed !')
            return False

        if self.slots[slot - 1] == '3722':  #3722 card
            if switch <= 96 and switch >= 1:
                return True
            elif 911 <= switch <= 916:   #backplane connections
                return True
            else:
                print('Daq3706.checkSwitchNumber() - Invalid switch number !')
                return False4
        elif self.slots[slot - 1] == '3720':
            if switch <= 60 and switch >= 1:
                return True
            elif 911 <= switch <= 916:   #backplane connections
                return True
            else:
                print('Daq3706.checkSwitchNumber() - Invalid switch number !')
                return False
        elif self.slots[slot - 1] == '3721':
            if switch <= 42 and switch >= 1:
                return True
            elif 911 <= switch <= 916:   #backplane connections
                return True
            else:
                print('Daq3706.checkSwitchNumber() - Invalid switch number !')
                return False
        elif self.slots[slot - 1] == '3723':
            if switch <= 60 and switch >= 1:
                return True
            elif 911 <= switch <= 916:   #backplane connections
                return True
            else:
                print('Daq3706.checkSwitchNumber() - Invalid switch number !')
                return False
        else:
            print('Daq3706.checkSwitchNumber() - Unsupported slot type !')
            return False
            
#==================================================================
if __name__ == '__main__':      #self test   

    visaName = 'K3706'     #default VISA name for selftest

    print(copyr) 
    """
    # checkList() test
    dvm = Daq3706('a', visaName)    #create device class instance
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
        dvm = Daq3706(rm, visaName)    #create device class instance
        dvm.open()
        dvm.scanSlots()
    except Exception:
        rm.close()
        sys.exit(2)
        
    reslt = False
    try:
        dvm.controlSwitch(1001, True)
        time.sleep(.1)        
        dvm.controlSwitch(1001, False)
        time.sleep(.1)        

        if dvm.configDmm('dcvolts', 10, 1):  #fnc, rng, NPLC
            v = dvm.readSwitch(1001)
            if v != False:
                print('Measured %f' % v)
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
    
