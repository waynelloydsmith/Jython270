#!/usr/bin/env jython
# coding: utf8
# console.py

"""
Jython Console with Code Completion

This uses the basic Jython Interactive Interpreter.
The UI uses code from Carlos Quiroz's 'Jython Interpreter for JEdit' http://www.jedit.org
this code is meant to be run by a java shell i.e its embedded
the java shell is located in
/mnt/DATA/home/wayne/source/moneydance/mone…om/moneydance/modules/features/jython270/main.java
does all the following
        pyi.exec("import sys");
        pyi.exec ("import os");
        pyi.exec("sys.path.append('/opt/moneydance/scripts/')");
        pyi.exec("sys.path.append(r'/opt/moneydance/scripts/jython270/')");
        pyi.exec("os.chdir('/opt/moneydance/scripts')");
        pyi.exec("from console import main"); //this starts the jython script console.py
        PyObject main = pyi.get("main");  // Returns the value of a variable in the local namespace.
        pyi.set("moneydance", getUnprotectedContext()); // sets the all important moneydance hook
        pyi.exec ("execfile('configConsole.py')");

some of it could be moved into console.py but ....
.................................configConsole.py does the following
import time
import sys
import os
from java.lang import System
execfile("CleanOut_sys_modules.py") # looks for /opt/moneydance/scripts modules in sys.modules
sys.path.append("/opt/moneydance/scripts")
import scriptsIPC # declares Moneydance , accountNames ,csvFile , and IMPORT
scriptsIPC.MoneyDance = moneydance  ... makes moneydance availeable to all
.................
aside preImport.py uses scriptsIPC.IMPORT to __import__ stuff.

so if you run console.py from a jython console all the stuff above will be missing
I can see some duplication
maybe use full paths for testing or
do the sys.path.appends here for testing
I only need the "sys.path.append('/opt/moneydance/scripts/')" for now
I added a TESTING variable to help control this
"""

from javax.swing import JFrame, JScrollPane, JPanel, JTextPane, Action, KeyStroke, WindowConstants
from javax.swing.text import JTextComponent, TextAction, SimpleAttributeSet, StyleConstants
from javax.swing import JToolBar
from javax.swing import JButton
from java.awt import Color, Font, Point
from java.awt.event import  InputEvent, KeyEvent, WindowAdapter
from java.awt import BorderLayout
from java.awt import Toolkit
from java.awt.datatransfer import DataFlavor
from java.lang import System


# need this -> sys.path.append(r'/opt/moneydance/scripts/jython270/') for console.py etc. imports to work includeing the '/' on the end
# above is done by main.java or CWD to it and run jython fron there for testing

import jintrospect
from popup import Popup
from tip import Tip
from history import History

import sys
from org.python.util import InteractiveConsole
from code import InteractiveInterpreter
sys.ps1 = '>>> '
sys.ps2 = '... '

__author__ = "Don Coleman <dcoleman@chariotsolutions.com>" # modified by waynelloydsmith@gmail.com .. web site is still valid dec 30 2025

import re
# allows multiple imports like "from java.lang import String, Properties"
_re_from_import = re.compile("from\s+\S+\s+import(\s+\S+,\s?)?")

try:
    True, False
except NameError:
    (True, False) = (1, 0)

TESTING = False # for running under the jython console instead of under moneydance


class Console:
    PROMPT = sys.ps1 # >>>
    PROCESS = sys.ps2  # ...
#    PROMPT = '>>>'
#    PROCESS = '...'
    BANNER = ["Jython Completion Shell", InteractiveConsole.getDefaultBanner()]
    DEBUG = False
    DEBUG2 = False
    more = False # the Jesus bolt for runsource
    logFile = None

  
    include_single_underscore_methods = False
    include_double_underscore_methods = False
    last_key_pressed_was_enter = False

    def __init__(self, namespace=None):
        """
            Create a Jython Console.
            namespace is an optional and should be a dictionary or Map
        """
        self.history = History(self) # this is in history.py

        if namespace != None:
            self.locals = namespace
        else:
            self.locals = {}

        self.buffer = [] # buffer is a list of inputs used for multi-line commands


        self.logFile = open('/home/wayne/.jythonconsole.log', 'a') # append

# redirect System.out to the log  file  .. dropped this .. afraid it might break moneydance
#        import java.io.PrintStream as PrintStream
#        import java.io.FileOutputStream as FileOutputStream
#        import java.io.File as File
#
#        file2stream = FileOutputStream(File('/home/wayne/.jythonconsole.log'), True) # True for append mode
#        printStream = PrintStream(file2stream)
#
#        # Save original System.out
#        #originalSystemOut = System.out
#
#        # Redirect System.out
#        System.setOut(printStream)


        self.interp = Interpreter(self, self.locals , self.logFile) # this writes errors to the text_pane and logFile
                                        # interp does not write to stderr because its write() method  has been overridden

        sys.stdout = StdOutRedirector(self) # redirects stdout to the text_pane.

#        self.log_tee = self.TeeStdOut(self.logFile) # taps into stdout
#        self.log_tee2 = self.TeeStdErr(self.logFile) # taps into stderr

        sys.stdout =  self.Tee(sys.stdout, self.logFile) # new jan 18 2026 taps into stdout for logging

        sys.stderr = self.Tee(sys.stderr, self.logFile) # new jan 17 2026  taps into stderr for logging



        self.text_pane = JTextPane(keyTyped = self.keyTyped, keyPressed = self.keyPressed)

        self.__initKeyMap()

        self.doc = self.text_pane.document
        self.__propertiesChanged()
        self.__inittext()
        self.initialLocation = self.doc.createPosition(self.doc.length-1)

        # Don't pass frame to popups. JWindows with null owners are not focusable
        # this fixes the focus problem on Win32, but make the mouse problem worse
        self.popup = Popup(None, self.text_pane)
        self.tip = Tip(None)

        # get fontmetrics info so we can position the popup
        metrics = self.text_pane.getFontMetrics(self.text_pane.getFont())
        self.dotWidth = metrics.charWidth('.')
        self.textHeight = metrics.getHeight()

        # add some handles to our objects
        self.locals['console'] = self
#        System.err.println("System.out assignment:"+ str(System.out))
#        System.err.println("System.err assignment:"+ str(System.err))
#        System.out.println("********************************888888 Testing System.out")
#        System.out.write("********************************888888 Testing System.out")
#        System.out.flush()
#        sys.stderr.write("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx Done the Console __init__\n") # tested the log file

    def insertText(self, text):
#        if self.DEBUG == True : sys.stderr.write("insertText " + text + "\n")
        """insert text at the current caret position"""
        # seems like there should be a better way to do this....
        # might be better as a method on the text component?
        caretPosition = self.text_pane.getCaretPosition()
        self.text_pane.select(caretPosition, caretPosition)
        self.text_pane.replaceSelection(text)
        self.text_pane.setCaretPosition(caretPosition + len(text))

    def getText(self):
        """get text from last line of console"""
        offsets = self.__lastLine()
        text = self.doc.getText(offsets[0], offsets[1]-offsets[0])
### need to strip the >>> prompt off of the source line
# what about the ...
        source2 = text.lstrip('>')
        source2 = text.replace('...','') # Dec 27 2025
        source3 = source2.rstrip()
        if self.DEBUG == True: sys.stderr.write("getText source3 "+ source3 + "\n")
        return source3

    def getDisplayPoint(self):
        """Get the point where the popup window should be displayed"""
        screenPoint = self.text_pane.getLocationOnScreen()
        caretPoint = self.text_pane.caret.getMagicCaretPosition()

        # BUG: sometimes caretPoint is None
        # To duplicate type "java.aw" and hit '.' to complete selection while popup is visible

        x = screenPoint.getX() + caretPoint.getX() + self.dotWidth
        y = screenPoint.getY() + caretPoint.getY() + self.textHeight
        return Point(int(x),int(y))

    def hide(self, event=None):
        """Hide the popup or tip window if visible"""
        if self.popup.visible:
            self.popup.hide()
        if self.tip.visible:
            self.tip.hide()

    def hideTip(self, event=None):
        self.tip.hide()
        self.insertText(')')

    def showTip(self, event=None):
        # get the display point before writing text
        # otherwise magicCaretPosition is None
        displayPoint = self.getDisplayPoint()

        if self.popup.visible:
            self.popup.hide()
        
        line = self.getText()

        self.insertText('(')
        
        (name, argspec, tip) = jintrospect.getCallTipJava(line, self.locals)

        if tip:
            self.tip.showTip(tip, displayPoint)
            
    def showPopup(self, event=None):
        """show code completion popup"""
#        sys.stderr.write("showPopup self line=\n")
        try:
            line = self.getText()
#            sys.stderr.write(line)
            list = jintrospect.getAutoCompleteList(line, self.locals, includeSingle=self.include_single_underscore_methods, includeDouble=self.include_double_underscore_methods)
            if len(list) > 0:
                self.popup.showMethodCompletionList(list, self.getDisplayPoint())
#            else:    
#                sys.stderr.write("showPopup self empty list\n")

        except:
#            print >> sys.stderr, "Error getting completion list: ", e
            sys.stderr.write("Error getting completion list: ")
            #traceback.print_exc(file=sys.stderr)

    def inLastLine(self, include = 1):
        """ Determines whether the cursor is in the last line """
        limits = self.__lastLine()
        caret = self.text_pane.caretPosition
        if self.text_pane.selectedText:
            caret = self.text_pane.selectionStart
        if include:
            return (caret >= limits[0] and caret <= limits[1])
        else:
            return (caret > limits[0] and caret <= limits[1])

# all the buffer stuff below is to glue the first >>> command and the remaining ... commands together
#  through testing I proved that runsource does no buffering push does

    def enter(self, event=None):
        """ Triggered when enter is pressed """
        text = self.getText()
#        if self.DEBUG == True: sys.stderr.write("text " + text + '\n')
        self.printResult("\n")
        self.buffer.append(text)        # save this line in the buffer list  .. for multi line commands save it in the buffer
        source = "\n".join(self.buffer) # replace what we just got with whats in the buffer. yes all the items in the list
                                        # above converts the list to a string with \n as a separator between items could be a long line
        source = "\n" + source + "\n"
        if text == '':                  # trigger to run runsource
                self.more = False
# enter gets pressed many times during the collection of the complete line of commands
# how do we know when the user is done. pressing enter with text == ''
        self.last_key_pressed_was_enter = True

#  some testing
#        source = "if True:\n    print('x')\nelse:\n    print('y')\n"  # runsource was happy with this and printed x
#        source = "if False:\n    print('x')\nelse:\n    print('y')\n"  # runsource was happy with this and printed y
#        source = "if (1 == 1 ):\n\tprint('x')\nelse:\n\tprint('y')\n"  # try tabs runsource was happy with this and printed x
#        source = "if (1 == 1 ):\n"  # this should produce a ... more should be False .. this test failed
#        more = self.interp.runsource(source) # execute the command with runsource
#        source = "\tprint('x')\nelse:\n\tprint('y')\n" # this should complete the command >>> more should be true

        if not self.more:
              if self.DEBUG2 == True: sys.stderr.write("console.py running runsource \n")
              self.more = self.interp.runsource(source) # execute the command with runsource # we don't do this every time enter is pressed

#        if self.DEBUG == True: sys.stderr.write("last_key_pressed_was_enter " + str(self.last_key_pressed_was_enter) + "\n")
#        if self.DEBUG == True: sys.stderr.write("more " + str(self.more) + "\n")
#        if self.DEBUG == True: sys.stderr.write('source '+ source) # source already has a \n on both ends of it
#        if self.DEBUG == True: sys.stderr.write('buffer '+str(self.buffer)+'\n')

        if self.more:                  # this seems backwards if its False all is well .. if its True we need to collect input
            self.printOnProcess() # ...
        else:
            self.resetbuffer()
            self.printPrompt()  # >>>
        if self.DEBUG == True: sys.stderr.write("appending text to history " + text + '\n')
        self.history.append(text)

        self.hide()

 #   def quit(self, event=None):
 #       sys.exit()

    def resetbuffer(self):
        self.buffer = []

    def home(self, event):
        """ Triggered when HOME is pressed """
        if self.inLastLine():
            # go to end of PROMPT
#            self.text_pane.caretPosition = self.__lastLine()[0]
            self.text_pane.caretPosition = self.__lastLine()[0] + len(Console.PROMPT)
        else:
            lines = self.doc.rootElements[0].elementCount
            for i in xrange(0,lines-1):
                offsets = (self.doc.rootElements[0].getElement(i).startOffset, \
                    self.doc.rootElements[0].getElement(i).endOffset)
                line = self.doc.getText(offsets[0], offsets[1]-offsets[0])
                if self.text_pane.caretPosition >= offsets[0] and \
                    self.text_pane.caretPosition <= offsets[1]:
                    if line.startswith(Console.PROMPT) or line.startswith(Console.PROCESS):
                        self.text_pane.caretPosition = offsets[0] + len(Console.PROMPT)
                    else:
                        self.text_pane.caretPosition = offsets[0]

    def end(self, event):
        if self.inLastLine():
            self.text_pane.caretPosition = self.__lastLine()[1] - 1

    # TODO look using text_pane replace selection like self.insertText
    def replaceRow(self, text):
        """ Replaces the last line of the textarea with text """
        if self.DEBUG == True: sys.stderr.write("replaceRow\n")
        if self.DEBUG == True: sys.stderr.write("RR text "+text+"\n")
        offset = self.__lastLine()
        last = self.doc.getText(offset[0], offset[1]-offset[0])
        if self.DEBUG == True: sys.stderr.write("RR last "+last+"\n")
        if self.DEBUG == True: sys.stderr.write("RR offset "+str(offset)+"\n")
        if last != "\n":
            self.doc.remove(offset[0], offset[1]-offset[0]-1)
        text = text.replace("\n","") #  jan 16 2026
        self.__addOutput(self.infoColor, text)
             
    def delete(self, event):
        """ Intercepts delete events only allowing it to work in the last line """
        if self.DEBUG == True: sys.stderr.write("delete \n")
        if self.inLastLine():
            if self.text_pane.selectedText:
                self.doc.remove(self.text_pane.selectionStart, self.text_pane.selectionEnd - self.text_pane.selectionStart)
            elif self.text_pane.caretPosition < self.doc.length:
                self.doc.remove(self.text_pane.caretPosition, 1)

    def backSpaceListener(self, event=None):   # left Arrow too ?
        """ Don't allow backspace or left arrow to go over prompt """
#        if self.DEBUG == True: sys.stderr.write("backSpace \n")
# for some reason this calce is out by 4 characters .. len(Console.PROMPT)
# note: getCaretPosition returns 0 at top left corner .
# len is always 4
# lastLine()[0] seems to be the bottom left hand corner in front of the caret like 426 when the corner is 422 . beginning of the lastLine
# was        onFirstPosition = self.text_pane.getCaretPosition() <= ( self.__lastLine()[0] + len(Console.PROMPT) )
        onFirstPosition = self.text_pane.getCaretPosition() <= ( self.__lastLine()[0] ) # works Dec 30 2025
#      works ok now
#        if self.DEBUG == True: sys.stderr.write("backSpace lastLine:" + str(self.__lastLine()[0])+"\n") # 146
#        if self.DEBUG == True: sys.stderr.write("backSpace len:" + str(len(Console.PROMPT))+"\n")        # 4
#        if self.DEBUG == True: sys.stderr.write("backSpace getCaret:" + str(self.text_pane.getCaretPosition())+"\n" ) # 150
#        if self.DEBUG == True: sys.stderr.write("backSpace onFirstPosition:" + str(onFirstPosition)+"\n" ) # True
#
#        if onFirstPosition:
#	  buff = "backSpaceListener  " + "True" + "\n"
#	else:
#	  buff = "backSpaceListener  " + "False" + "\n"	  
#        if self.DEBUG == True: sys.stderr.write(buff)  
#	buff = "backSpaceListener  " + str(self.text_pane.getCaretPosition()) + "\n"
#        if self.DEBUG == True: sys.stderr.write(buff)  
#	buff = "backSpaceListener  " + str(self.__lastLine()[0]) + "\n"
#        if self.DEBUG == True: sys.stderr.write(buff)                 
        if onFirstPosition and not self.text_pane.selectedText:
            event.consume()
                                       
    def spaceTyped(self, event=None):
        """check if we should complete on the space key"""
        ### this popup only gets displayed at the end of a command like "from org.python.core import PyCell" so you can pick PyCell from a list
        matches = _re_from_import.match(self.getText())
#       matches = True
#        if matches:
#	  buff = "spaceTyped  " + "True" + "\n"
#	else:
#	  buff = "spaceTyped  " + "False" + "\n"	  
#        if self.DEBUG == True: sys.stderr.write(buff)       
#	buff = "spaceTyped  " + str(self.getText()) + "\n"
#       if self.DEBUG == True: sys.stderr.write(buff)  
        
        if matches:
            self.showPopup()

    def killToEndLine(self, event=None):
        if self.inLastLine():
            caretPosition = self.text_pane.getCaretPosition()
            self.text_pane.setSelectionStart(caretPosition)
            self.text_pane.setSelectionEnd(self.__lastLine()[1] - 1)
            self.text_pane.cut()

    def paste(self, event=None):
        # if getText was smarter, this method would be unnecessary
        if self.inLastLine():
            clipboard = Toolkit.getDefaultToolkit().getSystemClipboard()
            clipboard.getContents(self.text_pane)
            contents = clipboard.getData(DataFlavor.stringFlavor)

            lines = contents.split("\n")
            for line in lines:
                self.insertText(line)
                if len(lines) > 1:
                    self.enter()

    def keyTyped(self, event):
        #print >> sys.stderr, "keyTyped", event.getKeyCode()
        if not self.inLastLine():
            event.consume()

    def keyPressed(self, event):
        if self.popup.visible:
            self.popup.key(event)
        #print >> sys.stderr, "keyPressed", event.getKeyCode()
        if event.keyCode == KeyEvent.VK_BACK_SPACE or event.keyCode == KeyEvent.VK_LEFT:
            self.backSpaceListener(event)

#    def keyboardInterruptkeyboardInterruptkeyboardInterrupt(self, event=None):
#        """ Raises a KeyboardInterrupt"""
#        self.hide()
#        self.interp.runsource("raise KeyboardInterrupt\n")
#        self.resetbuffer()
#        self.printPrompt()
                
    # TODO refactor me
    def write(self, text):
        self.__addOutput(self.infoColor, text)

    def printResult(self, msg):
        """ Prints the results of an operation """
        if self.DEBUG == False: sys.stderr.write("printResult " + msg + '\n')
#        import traceback
#        traceback.print_stack() # didn't go back far enough
        if '>>>' in msg : # this is because the 2.7.4 interpreter is sending >>> to stdout when it starts up .. 2.7.2 doesn't
           sys.stderr.write("printResult ignoring " + msg + '\n')
           return
#        raise Exception ("stop")

#        if msg != '\n':
#           self.__addOutput(self.text_pane.foreground,str(msg) +  "\n" )
#         self.__addOutput(self.text_pane.foreground, "\n" + str(msg))
        self.__addOutput(self.text_pane.foreground,str(msg))
        
####        self.__addOutput(self.text_pane.foreground,"?" + str(msg))

    def printError(self, msg): 
        self.__addOutput(self.errorColor, str(msg))
####        self.__addOutput(self.errorColor, str(msg) + "\n")
####        self.__addOutput(self.errorColor, "\n" + str(msg))

    def printOnProcess(self):
        """ Prints the process symbol ... """
####        self.__addOutput(self.infoColor, "\n" + Console.PROCESS) # dec 28 2025 too many \n s
        self.__addOutput(self.infoColor, Console.PROCESS)
####        self.__addOutput(self.infoColor, Console.PROCESS + "\n") # Dec 27 2025

    def printPrompt(self):
####        """ Prints the prompt """
        if self.last_key_pressed_was_enter == True:
           self.__addOutput(self.infoColor, Console.PROMPT)
           self.last_key_pressed_was_enter = False
        else:
           self.__addOutput(self.infoColor, "\n" + Console.PROMPT)
        
    def __addOutput(self, color, msg): # this only updates the document
        """ Adds the output to the text area using a given color """
        from javax.swing.text import BadLocationException # insertString may throw this
        style = SimpleAttributeSet()

        if color:
            style.addAttribute(StyleConstants.Foreground, color)
        formatted = ''.join('\\x%02x' % ord(byte) for byte in msg)

#        print(formatted)
        if self.DEBUG == True: sys.stderr.write("Bytes " +formatted+"\n") # print the bytes
        if self.DEBUG == True: sys.stderr.write("__addOutput msg "+ msg + "\n")
        if self.DEBUG == True: sys.stderr.write("__addOutput type " + str(type(msg)) + "\n")
        if self.DEBUG == True: sys.stderr.write("__addOutput current doc.length "+ str(self.doc.length) + "\n")
        if self.DEBUG == True: sys.stderr.write("__addOutput style "+ str(style) + "\n")
        if self.DEBUG == True: sys.stderr.write("__addOutput msg length "+ str(len(msg)) + "\n")


        self.doc.insertString(self.doc.length, msg, style) # updates the length .. this is the only call to this in this script

        self.text_pane.revalidate() # jan 26 2026
        self.text_pane.repaint()    # jan 26 2026

        if self.DEBUG == True: sys.stderr.write("__addOutput new doc.length "+ str(self.doc.length) + "\n")
        self.text_pane.caretPosition = self.doc.length
#        if self.DEBUG == True:
#                        sys.stderr.write("using insertText" + "\n")  # this worked I got two of everything on the screen
#                        self.insertText(msg);

    def __propertiesChanged(self):
        """ Detects when the properties have changed """
        self.text_pane.background = Color.white #jEdit.getColorProperty("jython.bgColor")
        self.text_pane.foreground = Color.blue #jEdit.getColorProperty("jython.resultColor")
        self.infoColor = Color.black #jEdit.getColorProperty("jython.textColor")
        self.errorColor = Color.red # jEdit.getColorProperty("jython.errorColor")

        family = "Monospaced" # jEdit.getProperty("jython.font", "Monospaced")
        size = 16 #jEdit.getIntegerProperty("jython.fontsize", 14)
        style = Font.PLAIN #jEdit.getIntegerProperty("jython.fontstyle", Font.PLAIN)
        self.text_pane.setFont(Font(family,style,size))

    def __inittext(self):
        """ Inserts the initial text with the jython banner """
        import sys
        self.doc.remove(0, self.doc.length)
        for line in "\n".join(Console.BANNER): # this is confusing does it one char at a time ???
            self.__addOutput(self.infoColor, line)
#            sys.stderr.write(line) # line is a single character with out any "\n"
#        raise Exception ("stop")
#        self.__addOutput(self.infoColor, '\n') # y\tack on the missing \n
        self.printPrompt()
        self.text_pane.requestFocus()

    def __initKeyMap(self):
      
#        os_name = System.getProperty("os.name")
#        if os_name.startswith("Win"):
#            exit_key = KeyEvent.VK_Z
#            interrupt_key = KeyEvent.VK_PAUSE # BREAK
#        else:
#            exit_key = KeyEvent.VK_D
#            interrupt_key = KeyEvent.VK_C

        keyBindings = [
            (KeyEvent.VK_ENTER, 0, "jython.enter", self.enter),
            (KeyEvent.VK_DELETE, 0, "jython.delete", self.delete), # back space is missing
            (KeyEvent.VK_HOME, 0, "jython.home", self.home),
            (KeyEvent.VK_LEFT, InputEvent.META_DOWN_MASK, "jython.home", self.home),
            (KeyEvent.VK_UP, 0, "jython.up", self.history.historyUp),
            (KeyEvent.VK_DOWN, 0, "jython.down", self.history.historyDown),
            (KeyEvent.VK_PERIOD, 0, "jython.showPopup", self.showPopup),
            (KeyEvent.VK_ESCAPE, 0, "jython.hide", self.hide),

            ('(', 0, "jython.showTip", self.showTip),
            (')', 0, "jython.hideTip", self.hideTip),
#            (exit_key, InputEvent.CTRL_MASK, "jython.exit", self.quit),
            (KeyEvent.VK_SPACE, InputEvent.CTRL_MASK, "jython.showPopup", self.showPopup),
            (KeyEvent.VK_SPACE, 0, "jython.space", self.spaceTyped),

            # explicitly set paste since we're overriding functionality
            (KeyEvent.VK_V, Toolkit.getDefaultToolkit().getMenuShortcutKeyMask(), "jython.paste", self.paste),

            # Mac/Emacs keystrokes
            (KeyEvent.VK_A, InputEvent.CTRL_MASK, "jython.home", self.home),
            (KeyEvent.VK_E, InputEvent.CTRL_MASK, "jython.end", self.end),
            (KeyEvent.VK_K, InputEvent.CTRL_MASK, "jython.killToEndLine", self.killToEndLine),
            (KeyEvent.VK_V, InputEvent.CTRL_MASK, "jython.paste", self.paste),
            
#            (KeyEvent.VK_C, InputEvent.CTRL_MASK, "jython.keyboardInterrupt", self.keyboardInterrupt),
            ]

        keymap = JTextComponent.addKeymap("jython", self.text_pane.keymap)
        for (key, modifier, name, function) in keyBindings:
            keymap.addActionForKeyStroke(KeyStroke.getKeyStroke(key, modifier), ActionDelegator(name, function))
        self.text_pane.keymap = keymap
        
    def __lastLine(self):
        """ Returns the char offests of the last line """
        lines = self.doc.rootElements[0].elementCount
        offsets = (self.doc.rootElements[0].getElement(lines-1).startOffset, \
                   self.doc.rootElements[0].getElement(lines-1).endOffset)
        line = self.doc.getText(offsets[0], offsets[1]-offsets[0])
        if len(line) >= 4 and (line[0:4]==Console.PROMPT or line[0:4]==Console.PROCESS):
            return (offsets[0] + len(Console.PROMPT), offsets[1])
        return offsets

#    class TeeStdOut(object): # duplicate the stdout to a file
#        def __init__(self,logFile):
#                self.logFile = logFile
#                self.stdout = sys.stdout
#                sys.stdout = self  # redirects all standard output to a custom object named TeeStdOut
#
#        def write(self, data):
#                self.logFile.write(data)
#                self.stdout.write(data)
#                self.logFile.flush()


#    class TeeStdErr(object): # duplicate the stderr to a file
#        def __init__(self,logFile):
#                self.logFile = logFile
#                self.stderr = sys.stderr
#                sys.stderr = self  # redirects all standard errors to a custom object named TeeStdErr
#
#        def write(self, data):
#                self.logFile.write(data)
#                self.stderr.write(data)
#                self.logFile.flush()


    class Tee(object):  # jan 17 2026 other one wasn't working
        def __init__(self, stream1, stream2):
                self.stream1 = stream1
                self.stream2 = stream2

        def write(self, data):
                self.stream1.write(data)
                self.stream2.write(data)
#                self.flush()

        def flush(self):
                self.stream1.flush()
                self.stream2.flush()


    global createToolBar
    def createToolBar(panel):
        if TESTING:
          import sys
          sys.path.append('/opt/moneydance/scripts/') # need this for testing with jython CWD is scripts/jython270
        import os
        import threading


        def on_button1_click(event): # clear screen
           consoleTextPane.setText("") # this cleared the screen
           if Console.more:
              consoleTextPane.setText(Console.PROCESS) # this shows up blue
           else:
              consoleTextPane.setText(Console.PROMPT) # this shows up blue



        def on_button2_click(event): # open the console.log which doesn't exist
            def start_editor_task():
              editor = os.getenv("EDITOR")
              home = os.getenv("HOME")
              file2open = home+ "/.jythonconsole.log"
#              print('editor '+editor+'\n')
#              print('home '+home+'\n')
#              print('file2open '+file2open+'\n')
              command = editor+" "+ file2open
#              print ("command "+ command + '\n')
              stat = os.system(command) # works but weird things happen
#              print ("stat "+ str(stat) + '\n') # should be zero .. this prints after you close kwrite ????
                                                # maybe stat is only useful if it fails then stat will not be 0 ???
            editor_thread = threading.Thread(target=start_editor_task, name="TextEditorThread")
            editor_thread.start()

        def on_button3_click(event):
#           print "Button3 in panel was clicked!"
            import runScripts
            runScripts.runScripts()
#           import scriptsIPC
#           scriptsIPC.IMPORT = 'runScripts'
#           execfile('/opt/moneydance/scripts/PreImport.py') # need full path if its not in CWD

        def on_button4_click(event): # open the command history
            def start_editor_task():
              home = os.getenv("HOME")
              editor = os.getenv("EDITOR")
              file2open = home+ "/.jythonconsole.save"
#              print('editor '+editor+'\n')
#              print('home '+home+'\n')
#              print('file2open '+file2open+'\n')
              command = editor+" "+ file2open
#              print ("command "+ command + '\n')
              stat = os.system(command) # works but weird things happen
#              print ("stat "+ str(stat) + '\n') # this don't work ???? should be zero
            editor_thread = threading.Thread(target=start_editor_task, name="TextEditorThread")
            editor_thread.start()


        def on_button5_click(event):# Open the moneydance errlog.txt
            def start_editor_task():
              home = os.getenv("HOME")
              editor = os.getenv("EDITOR")
              stat = os.system(editor + " " + home + "/.moneydance/errlog.txt") # stat should be 0
            editor_thread = threading.Thread(target=start_editor_task, name="TextEditorThread")
            editor_thread.start()

        def on_button6_click(event): # open README.txt
            def start_editor_task():
              editor = os.getenv("EDITOR")
              stat = os.system(editor + " " + "/opt/moneydance/scripts/jython270/README.txt") # stat should be 0
            editor_thread = threading.Thread(target=start_editor_task, name="TextEditorThread")
            editor_thread.start()



        #Create the toolbar.
        toolBar = JToolBar()
        panel.add(toolBar, BorderLayout.PAGE_START);      # stick it on the JPanel

        #first button
        button1 = JButton()
        button1.setText("Clear Screen")
        button1.addActionListener(on_button1_click) # it just wants a function to call
        button1.setToolTipText("Click to Clear the Console.")
        button1.setActionCommand("button1 pressed")   # get this instead of Button1 in the handler
        button1.setFont(Font("Arial", Font.BOLD , 10)) # PLAIN or BOLD or Italic
        toolBar.add(button1);

        #second button
        button2 = JButton()
        button2.setText("View Log File") # there is no log file for console.py only a command history file
                                         # the log file on JConsole2026 is very handy. its everything except the errors.
        button2.addActionListener(on_button2_click)  # was this ... below is a poor mans way to get multi LINE TIPS
        button2.setToolTipText("<html>"
                                         + "Click to Open the log File with EDITOR."
                                         +"<br>"
                                         + "You must set EDITOR in your env."
                                         +"<br>"
                                         + "export EDITOR=kwrite."
                                         +"<br>"
                                         + "Put it in /etc/profile.d/local.sh."
                                         +"</html>")
        button2.setActionCommand("button2 pressed")
        button2.setFont(Font("Arial", Font.BOLD, 10))
        toolBar.add(button2)

        # third button
        button3 = JButton()
        button3.setText("Start runScripts.py")
        button3.addActionListener(on_button3_click) # was this
        button3.setToolTipText("Click to run the runSripts.py file.")
        button3.setActionCommand("button3 pressed")
        button3.setFont( Font("Arial", Font.BOLD , 10))
        toolBar.add(button3)

        button4 = JButton() # Change Command History
        button4.setText("Command History")
        button4.addActionListener(on_button4_click)
        button4.setToolTipText("Click to edit the command history file.")
        button4.setActionCommand("button4 pressed")
        button4.setFont( Font("Arial", Font.BOLD , 10))
        toolBar.add(button4)

        button5 = JButton() # Open the errlog
        button5.setText("Open errlog")
        button5.addActionListener(on_button5_click)
        button5.setToolTipText("Click to open the moneydance errlog.txt file.")
        button5.setActionCommand("button5 pressed")
        button5.setFont( Font("Arial", Font.BOLD , 10))
        toolBar.add(button5)

        button6 = JButton() # Open console README.txt
        button6.setText("Open Readme")
        button6.addActionListener(on_button6_click)
        button6.setToolTipText("Click to vie the Readme file.")
        button6.setActionCommand("button6 pressed")
        button6.setFont( Font("Arial", Font.BOLD , 10))
        toolBar.add(button6)



class ActionDelegator(TextAction):
    """
        Class action delegator encapsulates a TextAction delegating the action
        event to a simple function
    """
    def __init__(self, name, delegate):
        TextAction.__init__(self, name)
        self.delegate = delegate

    def actionPerformed(self, event):
        if isinstance(self.delegate, Action):
            self.delegate.actionPerformed(event)
        else:
            self.delegate(event)

class Interpreter(InteractiveInterpreter):
    def __init__(self, console, locals, logFile):
        InteractiveInterpreter.__init__(self, locals)
        self.console = console
        self.logFile = logFile
        
    def write(self, data):
        # send all output to the textpane
        # KLUDGE remove trailing linefeed
#        self.console.printError(data[:-1])
#        global logFile
        self.logFile.write(data)
        self.logFile.flush()
        self.console.printError(data)
        
# redirect stdout to the textpane it needs a flush
class StdOutRedirector:
    DEBUG = True
    def __init__(self, console):
        self.console = console
        
    def write(self, data):
         if self.DEBUG == True: sys.stderr.write("StdOutRed "+ data + "\n")
#         raise Exception ("stop")
         self.console.printResult(data)
     # Add the missing flush method needed by the logger
    def flush(self):                           # jan 24 2026 didn't work
         if self.DEBUG == True: sys.stderr.write("StdOutRed Flushing" + "\n")
#         self.console.flush()
#        self.console.printResult(data)         # fudge
         pass # The 'pass' keyword means it does nothing if you don't need explicit flushing within the class


class JythonFrame(JFrame):
    def __init__(self):
        self.title = "Jython270"
        self.size = (700, 400) # was 600, 400
        self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)
"""        
        try:
            self.setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE)
        except:
            # assume jdk < 1.4
            self.addWindowListener(KillListener())
            self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)

class KillListener(WindowAdapter):
    
    Handle EXIT_ON_CLOSE for jdk < 1.4
    Thanks to James Richards for this method
   
    def windowClosed(self, evt):
        from java.lang.System import System
        System.exit(0)
"""        
        
def main(namespace=None):
    global frame
    frame = JythonFrame()
    console = Console(namespace)
    global pnl
    pnl = JPanel(BorderLayout());     #new
    frame.add(pnl);                   #new
    global consoleTextPane            # used to clear the screen
    consoleTextPane = console.text_pane
    global scrollPane
    scrollPane = JScrollPane(consoleTextPane) #new
    pnl.add(scrollPane, BorderLayout.CENTER); #new
    createToolBar(pnl)
#    frame.getContentPane().add(JScrollPane(console.text_pane))
    frame.visible = True
  
if __name__ == "__main__":
    main()
    
