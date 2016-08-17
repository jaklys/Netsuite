"""
VISA library simulation for testing measurement setups without real
instruments available. Mimics interface of the VISA library.
Prints actions done in VISA.
Use: replace the 'import visa' command in module you want to debug
     with 'import visasim as visa' command
visasim.py (C) J.M.,rev.23-Jan-15
"""

copyr = 'visasim.py (C) J.M.,rev.23-Jan-15'

class ResourceManager:
    """
    Creates/deletes device instances
    Keeps list of assigned devices    
    """
    def __init__(self):
        """
        Initializes counter of assigned handles and list of devices
        Returns ResourceManager class instance
        """
        self.devices = {}    #dictionary of assigned handles and visa names
        print('Resource manager created.')
            
    def get_instrument(self, visaName):
        """
        Creates device class instance, adds it to the dictionary.
        Device type could be defined here by input() if device simulation
        is required. Individual device classes can be subclassed then using
        the Device class as a base. They can overload generic responses of
        the base class with something more sophisticated.
        Input:      visa name
        Returns:    device class
        """
        dev = Device(self, visaName)    #creaste device instance
        self.devices[visaName] = dev    #add to dictionary
        print(visaName + ' instrument created.')
        return dev
    
    def close_instrument(self, visaName):
        """
        Removes device from list
        Input:      visa name
        Returns:    none
        """
        self.devices.pop(visaName)          #remove dictionary item
        print(visaName + ' instrument closed.')
        
    def close(self):
        """
        rm.close()  kills all issued devices
        """
        self.devices = {}    #garbage collector should delete device instances
        print('Resource manager closed.')

class Device:
    """
    Class whose instance is created when resource manager is asked for 
    a new instrument. This class can be used as a base for subclasses
    emulating individual device type emulators.
    """
    def __init__(self, rm, visaName):
        """
        Constructor only stores visaName and resource manager
        to be used in emulation of behavior of individual instruments in
        member functions.
        """
        self.visaName = visaName
        self.rm = rm
        
    def close(self):
        """
        Removes device from dictionary kept in resource manager
        """
        self.rm.close_instrument(self.visaName)
        
    def write(self, cmd):
        """
        Processes command strings sent to device via VISA interface.
        Only prints the received command now for debugging.
        """
        print(self.visaName + ': written "' + cmd + '"')
        
    def read(self):
        """
        Emulates reading from a device via VISA interface.
        Only returns some string now
        """
        print(self.visaName + ': read "+1.2E3"')
        return '+1.2E3'
    
    def ask(self, cmd):
        """
        Emulates asking the device for response by sending some command via
        the VISA interface.
        Only prints the received command now for debugging and
        returns some string
        """
        print(self.visaName + ': asked "' + cmd + '", returned "+2.34"')
        return '+2.34'
    
# Self test
if __name__ == '__main__':
    print(copyr)

    rm = ResourceManager()              #create resource manager class

    try:
        handle = rm.get_instrument('VISA')  #create device
        handle.write('Command')             #send a command
        reslt = handle.read()               #read result
        print(reslt)                        
        reslt = handle.ask('Query')         #ask for data
        print(reslt)
        handle.close()                      #close device
    except:
        raise   #default exception handling
    finally:
        rm.close()                          #close resource manager
    print('OK')
    
