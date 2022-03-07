package log4j.log;

import org.apache.log4j.Logger;
import org.apache.log4j.xml.DOMConfigurator;




public class LoggerA {
	
	private static Logger log = Logger.getLogger(LoggerA.class.getName());
	
	public static void prerequisite() {
		DOMConfigurator.configure("log4j.xml");
	}
	
	public static void error ( String message) {
		log.error(message);
	}
	
	public static void warning ( String message) {
		log.warn(message);
	}
	
	public static void info ( String message) {
		log.info(message);
	}
	
	

}
