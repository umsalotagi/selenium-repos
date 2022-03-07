package com.test;

import org.testng.Reporter;

public class LogReport {
	
	public static void info (String msg) {
		Reporter.log("INFO : "+msg, true);
		Reporter.log("<br>");
	}
	
	public static void error (String msg) {
		Reporter.log("ERROR : " + msg, true);
		Reporter.log("<br>");
	}

}
