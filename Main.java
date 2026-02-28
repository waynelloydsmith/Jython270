
package com.moneydance.modules.features.jython270;
//embeds a jython console called jython270 in a java framework
// the jython console code is in /opt/moneydance/scripts/jython270

import com.moneydance.apps.md.controller.FeatureModule;
import com.moneydance.apps.md.controller.FeatureModuleContext;
import com.moneydance.apps.md.controller.ModuleUtil;
import com.moneydance.apps.md.controller.UserPreferences;

//import com.moneydance.apps.md.model.*;
//import com.infinitekind.moneydance.model.*;

import java.io.*;
import java.util.*;
import java.text.*;
import java.awt.*;

//import org.python.core.*;
import org.python.core.PySystemState;
import org.python.core.PyObject;
import org.python.util.PythonInterpreter;
//import org.python.google.common.base.internal.Finalizer;
//import org.python.modules.errno;

//import org.python.util.InteractiveConsole;
//import java.util.Properties;
//import java.io.*;

import java.util.Properties; 
//import org.python.util.PythonInterpreter; 
import java.util.Enumeration; 
//import threading;
//#import pythonThread.destroy();
//import multiprocessing as mp;

public class Main extends FeatureModule {


  public void init() {
    // the first thing we will do is register this module to be invoked
    // via the application toolbar
    FeatureModuleContext context = getContext();
    try {
      context.registerFeature(this, "showconsole",
        getIcon("jpython_icon.gif"),
        getName());
    }
    catch (Exception e) {
      e.printStackTrace(System.err);
    }
  }

  public void cleanup() {
    closeConsole();
  }

  
  private Image getIcon(String action) {
    try {
    ClassLoader cl = getClass().getClassLoader();
      java.io.InputStream in =
        cl.getResourceAsStream("/com/moneydance/modules/features/jython270/jpython_icon.gif");
      if (in != null) {
        ByteArrayOutputStream bout = new ByteArrayOutputStream(1000);
        byte buf[] = new byte[256];
        int n = 0;
        while((n=in.read(buf, 0, buf.length))>=0)
          bout.write(buf, 0, n);
        return Toolkit.getDefaultToolkit().createImage(bout.toByteArray());
      }
    } catch (Throwable e) { }
    return null;
  }
  
  /** Process an invokation of this module with the given URI */
  public void invoke(String uri) {
    String command = uri;
    String parameters = "";
    int theIdx = uri.indexOf('?');
    if(theIdx>=0) {
      command = uri.substring(0, theIdx);
      parameters = uri.substring(theIdx+1);
    }
    else {
      theIdx = uri.indexOf(':');
      if(theIdx>=0) {
        command = uri.substring(0, theIdx);
      }
    }

    if(command.equals("showconsole")) {
//        runConsole();
//      embedExample();        //  changed from myextension
      showConsole();
    }    
  }

  public String getName() {
    return "Jython270";
  }

  private synchronized void showConsole() {
//        runConsole(); this is very different in myextension based on if we have a window
      embedExample(); // this function does not exist in myextension
  }
  
  FeatureModuleContext getUnprotectedContext() {
    return getContext();
  }

  synchronized void closeConsole() {
      System.gc(); // this is very different too based on our window
    }


//public class EmbedExample {

    public void embedExample() {  // function does not exist in myextension
    
//        from java.lang import System    
//        System.err.println("java.ext.dirs: " + System.getProperty("java.ext.dirs"));
//        System.err.println("java.class.path: " + System.getProperty("java.class.path"));
//        System.err.println("java.home: " + System.getProperty("java.home"));
//        System.err.println("java.library.path: " + System.getProperty("java.library.path"));
//        System.err.println("sun.boot.class.path: " + System.getProperty("sun.boot.class.path"));
        
        PySystemState.initialize();
        PythonInterpreter pyi = new PythonInterpreter();   
//        pyi.exec("import sys");
///        pyi.exec ("import os");  //  new feb 12 2023
//      pyi.exec("from definitions import definitions"); // could replace this with sys.path.append(r'/opt/moneydance/scripts/jython270/')
//      pyi.exec("for buff in definitions.ClassPathNames:\n  exec(buff)\n");
//        pyi.exec("sys.path.append('/opt/moneydance/scripts/')");
//        pyi.exec("sys.path.append(r'/opt/moneydance/scripts/jython270/')"); //  required  for jython270
//        pyi.exec("os.chdir('/opt/moneydance/scripts')");

//        pyi.exec ("try:\n  import scriptsIPC \nexcept:\n  sys.stderr.write('Jython270 failed to import scriptsIPC\\n')\n");
//        pyi.exec ("try:\n  scriptsIPC.IMPORT = 'runScripts'\nexcept:\n  sys.stderr.write('Jython270 fail 2set scriptsIPC.IMPORT\\n')\n");
//        pyi.exec ("try:\n  execfile('PreImport.py')\nexcept:\n  sys.stderr.write('Jython270 failed to exec PreImport.py\\n')\n");
// \\n represents a string containing a literal backslash character followed by the literal character 'n'.   ???????  guess write needs it
//        pyi.exec ("try:\n  execfile('runScripts.py')\nexcept:\n  sys.stderr.write('Jython failed to load runScripts.py\\n')\n"); //
//        pyi.exec ("del buff"); // buff not used
//        pyi.exec("sys.path.append(r'/home/wayne/source/jythonconsole-0.0.7x/')");  // console.py lives here its now in /opt/moneydance/scripts/jython270
//        pyi.exec("sys.path.append(r'/home/wayne/source/jython-installer-2.5.3/jython.jar')");        
//        pyi.exec("sys.path.append(r'/home/wayne/source/jython-installer-2.5.3/Lib/')"); // os.py lives here
//        pyi.exec("sys.path.append(r'/home/wayne/source/jython-installer-2.5.3/Lib/site-packages')");
//        pyi.exec("sys.path.append(r'/home/wayne/source/Moneydance/')"); // myscripts live here ... this fixed import errors on my ???.py files      
//        pyi.exec("sys.registry['java.class.path'] = sys.registry['java.class.path'] + ':/home/wayne/source/jython-installer-2.5.3/jython.jar'");
//        pyi.exec("sys.add_package('org.python.modules.errno')");  
//        pyi.exec("sys.add_extdir('/home/wayne/source/jython-installer-2.5.3/')");  
//        pyi.exec("sys.add_classdir('/home/wayne/source/jython-installer-2.5.3/')");  
//        pyi.exec("import os");
//        pyi.exec("buff = sys.registry['user.home']+'/.moneydance/scripts'"); 
//        pyi.exec("os.chdir(buff)"); // change the cwd for the execfile commands or use full paths
        pyi.exec("import sys");
        pyi.exec("sys.path.append(r'/opt/moneydance/scripts/jython270/')"); //  required  to find jython270 console,py
        pyi.exec("from console import main"); //runs the console.py file  ..it needs the path to jython270
        PyObject main = pyi.get("main");  // Returns the value of the variable main in the local namespace.
        pyi.set("moneydance", getUnprotectedContext()); // set the hook to moneydance
        pyi.set("Java_Parent", "jython270");
        pyi.exec ("execfile('/opt/moneydance/scripts/configConsole.py')");
        main.__call__(pyi.getLocals());  // why ?
    }
 }
