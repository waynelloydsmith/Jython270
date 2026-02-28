//embeds a jython console called jython270 in a java framework
// the jython console code is in /opt/moneydance/scripts/jython270

        pyi.exec("from console import main");                           this kicks in the jython code in  /opt/moneydance/scripts/jython270
pyi.exec("sys.path.append(r'/opt/moneydance/scripts/jython270/')"); //  required  for jython270
pyi.exec("os.chdir('/opt/moneydance/scripts')");
pyi.exec ("os.chdir('/opt/moneydance/scripts')");  this is duplicated in main.java

the java code is just enough to keep moneydance happy
it switches to jython as soon as possible

from org.python.util import InteractiveConsole
from code import InteractiveInterpreter

code doesn't seem to use the InteractiveConsole


This uses the basic Jython Interactive Interpreter.
The UI uses code from Carlos Quiroz's 'Jython Interpreter for JEdit' http://www.jedit.org

..........found this in the jython README
Jython Console - Jython Interactive Interpreter with Code Completion

Visit http://code.google.com/p/jythonconsole for more information.

Run the code:
  * Open a terminal or cmd prompt
  * cd jythonconsole-0.0.7
  * jython console.py
Hints:
  * <TAB> and <ENTER> choose method completion
  * remember to use the keyboard not the mouse
  * <ESC> makes the popup go away
Author:
  Don Coleman <dcoleman@chariotsolutions.com>
License:
  Read the COPYING.txt file.
these scripts are used by the moneydance jython270 extension
I have modified some of it waynelloydsmith.
