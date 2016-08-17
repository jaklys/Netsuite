import sys, time
import visa
import cdaq34972, csrc2722
import rudp
from testlog import*



class Errors:
    """
    Class for maintaining error counter among imported modules
    """
    def __init__(self):
        self.errorCount = 0      #clear counter at start

    def bumpError(self):
        self.errorCount += 1

    def getErrorCount(self):
        return self.errorCount

def chkLimits(name, value, Min, Max, unit = 'V', Hex = False):
    """
    Checks value against provided limits.
    If out of limits, logs the message, bumps errorCount
    Input:  name - signal name for logging
            value - value to be tested
            Min, Max - limits
            Hex - if True limits displayed in hex, float otherwise (by default)
    Return: True if OK, False if out of limits
    """

    #global Log
    if not Min < value < Max:
        if Hex:
            line = "%s:0x%X OUT OF LIMITS (0x%X, 0x%X). Test Failed !" %(name, value,  Min, Max)
        else:
            line = "%s:%F %s OUT OF LIMITS (%F, %f). Test Failed !" %(name, value, unit, Min, Max)
        Log.logError(line)
        Err.bumpError()
        return False
    if Hex:
        Log.logText('    '+'%s:0x%X expected range from:0x%X To: 0x%X. Test PASS !'% (name, value, Min, Max))
    else:
        Log.logText('    '+'%s:%F %s expected range From:%F %s To: %F %s. Test PASS !'% (name, value, unit, Min,unit, Max, unit))
    return True

def measureAndCheckSwich(switch, name, loLim, hiLim,mod = 'VOLT:DC' ):

    DMM.configScan(switch, mod)
    v = DMM.read()
    #Log.logValue(name, v, unit)
    chkLimits(name, v, loLim, hiLim)
    return v

def switchAndCheck(sw, name, loLim, hiLim, unit = 'V', delay = 0):
    """
    Close a switch, measure with actual scallist, check against limits.
    If out of limits, logs the message, bumps errorCount
    DMM and Log provided as globals
    Input:  sw - switch number
            name - signal name for logging
            loLim, hiLim - limits
            unit - unit of measured value
            delay - waiting between closing switch and reading, default 0
    Return: measured value if OK, exception if fails
    """

    v = DMM.readSwitch(sw, delay)
    #Log.logValue(name, v, unit)
    chkLimits(name, v, loLim, hiLim)
    return v

def setHandles(dmm, src, brd, log, err):
    """
    Provide needed class instances to the module for easy access
    These parameters can't be changed within the module
    Input:  dmm - 34972A DAQ
            src - U2722A source meter
            brd - SCU communication handle
            log - class for logging
            err - error counter
    Return: none
    """
    global DMM, SRC, BRD, Log, Err
    DMM = dmm
    SRC = src
    BRD = brd
    Log = log
    Err = err