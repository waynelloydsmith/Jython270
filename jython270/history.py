"""
 history.py - Handles the History of the jython console
 Copyright (C) 2001 Carlos Quiroz

 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU General Public License
 as published by the Free Software Foundation; either version 2
 of the License, or any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""
# waynelloydsmith grossly modified this script
# there is a list and a file
# when you start up the entire file is loaded into the list
# as new commands are entered they are appended to both the file and the list
# if you move up or down or values are pulled from the list to display
# the list and the file should match so you don't have to save the list to the file
# when the program shuts down.
# use the command history button to put what ever you like in the history file
# you will need to delete this file or delete line from it after it reaches 2000 lines
# I guess you could use the shutdown hook to chop the file down to size.
# the java shutdown hook was pretty neat once I figured it out.

from java.lang import System
#from java.lang import System, Runtime
#from java.lang import Runnable, Thread
import sys

class History:
    """
    Command line history
    """
    DEBUG2 = False

    default_history_file = System.getProperty("user.home") + '/.jythonconsole.save'
    MAX_SIZE = 2000

    def __init__(self, console, history_file=default_history_file):
        if self.DEBUG2 == True: sys.stderr.write("History __init__"+ "\n")
#        Runtime.getRuntime().addShutdownHook(Thread(self))
        self.history_file = history_file
        self.historyList = []
        self.loadHistory()
        self.console = console
        self.index = len(self.historyList) - 1
        self.last = ""

    def append(self, line): # this is called with text every time you hit enter
        if self.DEBUG2 == True: sys.stderr.write("History append:"+ str(line) + "\n")
        if line == None or line == '\n' or len(line) == 0:
            return

        if line != self.last: # avoids duplicates
            self.last = line
#            line = line.lstrip('>')                # dec 28 2025 don't want >>> in history I think
            self.histFile.write(line + '\n')
            self.historyList.append(line)
            self.console.logFile.write(line + '\n')
            self.histFile.flush()
            self.console.logFile.flush()
            
        self.index = len(self.historyList) - 1 # stay where we are

    def historyUp(self, event=None):
        if self.DEBUG2 == True: sys.stderr.write("historyUP"+ "\n")
        if self.DEBUG2 == True: sys.stderr.write("index "+ str(self.index) + "\n")
        if self.DEBUG2 == True: sys.stderr.write("inLastLine "+ str(self.console.inLastLine()) + "\n")
        if self.DEBUG2 == True: sys.stderr.write("len "+ str(len(self.historyList)) + "\n")

        if len(self.historyList) > 0 and self.console.inLastLine():
            self.console.replaceRow( self.historyList[self.index])
            self.index = max(self.index - 1, 0)

    def historyDown(self, event=None):
        if self.DEBUG2 == True: sys.stderr.write("historyDown"+ "\n")
        if len(self.historyList) > 0 and self.console.inLastLine():
            if self.index == len(self.historyList) - 1:
                self.console.replaceRow("")                            ## was commented out
            else:
                self.index = self.index + 1
                self.console.replaceRow(self.historyList[self.index])

    def loadHistory(self): # this is called by __init__
        if self.DEBUG2 == True: sys.stderr.write("loadhistory"+ "\n")
        self.histFile = open(self.history_file,'a+') # for read and append
#        except:
#            sys.stderr.write("history loadhistory FAILED2"+ "\n") # this is a big deal
#            pass
        self.histFile.seek(0) # set file pointer to begining of file for reading .. append resets this pointer
#        try:
        self.historyList= self.histFile.readlines()
        line_count = len(self.historyList) # this is just the list
        if self.DEBUG2 == True: sys.stderr.write("line_count "+ str(line_count) +"\n")
        if line_count > self.MAX_SIZE:
            sys.stderr.write("jython270 command history File is too Big "+ str(line_count) +"\n")
            sys.stderr.write("jython270 use the command history button to fix it\n")
#        except:
#            sys.stderr.write("history loadhistory FAILED"+ "\n") # this is a big deal
#            pass
        
        
