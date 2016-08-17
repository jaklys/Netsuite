# Class supporting logging of board tests
# testlog.py (C) J.M.,rev.16-Jan-16

import os, sys


class TestLog():
    """
    Supports logging and displaying of test results
    """
    copyr = 'testlog.py (C) J.M.,rev.16-Jan-16'

    def __init__(self, rootName, mainPath, extension='.log'):
        """
        Input: board - board name used for creation of default log file name
               mainPath - path to the test script, used to locate .\data dir
               extension - log file extension including dot
        """
        self.file = None
        self.rootName = rootName.upper()  # for file name construction
        self.fileName = self.rootName + '_0000' + extension
        self.path = mainPath
        self.extension = extension

    def openLog(self):
        """
        Fetches last log name '<board>_xxxx'.log from .\data\lastlog.txt, 
        creates log name ending with next number. Asks to enter log name
        suggesting the newly created one. Opens the file
        """
        # Check presence or create log directory
        lastSlash = self.path.rfind('\\')
        lastName = self.fileName  # default name
        if lastSlash == -1:
            self.path = '.\\data\\'
        else:
            self.path = self.path[:lastSlash + 1] + 'data\\'
        if not os.path.exists(self.path):
            try:
                os.mkdir(self.path)
            except Exception:
                print("Dir for log not found and can't be made !")
                raise
            print("Log directory " + self.path + " created !")
        # try to create new log from last log in lastlog.txt else create default        
        lastLogName = self.path + "lastlog.txt"
        try:
            lastLogFile = open(lastLogName, "r")
        except OSError:
            print('File lastlog.txt not found - default log name used !')
        else:  # last line of the file shall be last log name
            lastLine = None
            for line in lastLogFile:
                lastLine = line
            lastLogFile.close()

            if lastLine == None:
                print("lastlog.txt didn't provide any name - default used !")
            else:
                lastLine = lastLine.strip('\n')
                lastDot = lastLine.rfind('.')
                lastSlash = lastLine.rfind('\\')
                if lastDot != -1 and lastDot >= 5:
                    numberPos = lastDot - 4
                    try:
                        lastNumber = int(lastLine[numberPos:numberPos + 4])
                    except ValueError:
                        lastName = lastLine[lastSlash + 1:]
                        self.fileName = lastName
                    else:
                        number = lastNumber + 1
                        number = '%04d' % number  # to 4-char string
                        lastNumber = '%04d' % lastNumber
                        self.fileName = lastLine[:numberPos] + number + self.extension
                        lastName = lastLine[:numberPos] + lastNumber + self.extension
                else:
                    print('Unexpected name format in lastlog.txt - default used !')
        # Prompt user to enter the log name        
        hintName = self.fileName
        while True:
            print('Last log name: ' + lastName)
            print('Automatic generated log name: ' + hintName)
            newName = input('Log name (<CR> accept automatic, R<CR> repeat last): ')
            if newName == '':
                self.fileName = hintName
            elif newName == 'r' or newName == 'R':
                self.fileName = lastName
            else:
                self.fileName = newName + ".txt"
            logPath = self.path + self.fileName
            # check if file already exists
            if os.path.isfile(logPath):
                yn = input('File exists. Overwrite (Y/N)? ')
                if yn == 'y' or yn == 'Y':
                    break  # else chance to specify the file again
            else:  # new file
                break
        try:
            self.file = open(logPath, "w")
        except Exception:
            print('Opening log file failed - test aborted !')
            raise
        # add last log name to lastlog.txt
        try:
            lastLogFile = open(lastLogName, "a")
            lastLogFile.write(self.fileName + '\n')
            lastLogFile.close()
        except Exception:
            print('Updating lastlog.txt failed ! Test continuing...')
        print(logPath + ' file open for saving log.')
        return True

    def closeLog(self):
        """"
        Close log file, ignore if fails        
        """
        if self.file != None:
            try:
                self.file.close()
            except Exception:
                print('Closing the log file failed !')
                raise

    def logError(self, line):
        """
        Prepend mark to provided test to make it visible in the log       
        """
        line = '**** Error: ' + line
        print(line)  # display on screen
        if self.file != None:
            line = line + '\n'
            try:
                self.file.write(line)
            except Exception:
                print('Writing to log failed !')
                raise

    def logText(self, line):
        """
        Simply displays and puts to log file a line of text        
        """
        print(line)
        if self.file != None:
            line = line + '\n'
            try:
                self.file.write(line)
            except Exception:
                print('Writing to log failed !')
                raise

    def logValue(self, name, v, unit):
        """
        Displays and logs a line containing value name, value and unit        
        """
        line = '       '+'%-16s = %f %s' % (name, v, unit)
        print(line)
        if self.file != None:
            line = line + '\n'
            try:
                self.file.write(line)
            except Exception:
                print('Writing to log failed !')
                raise

    def flushLog(self):
        """
        Flushes file buffers
        """
        try:
            self.file.flush()
        except Exception:
            raise


# Self test
# ==========
if __name__ == '__main__':
    Log = TestLog('BoardName', sys.argv[0], '.csv')  # provide script path
    print(Log.copyr)
    try:
        Log.openLog
        Log.logText('text')
        Log.logError('Error')
        Log.logValue('name', 3.14, 'V')
        Log.closeLog()
    except Exception:
        print('Failed')
        raise
    print('OK')
    sys.exit(0)
