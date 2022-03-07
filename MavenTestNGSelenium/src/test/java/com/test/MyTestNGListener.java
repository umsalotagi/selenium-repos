package com.test;

import org.testng.ITestContext;
import org.testng.ITestListener;
import org.testng.ITestResult;
import org.testng.Reporter;

public class MyTestNGListener implements ITestListener{

	public void onFinish(ITestContext arg0) {
		LogReport.info("TESTNG : On Finish");
		
	}

	public void onStart(ITestContext arg0) {
		LogReport.info("TESTNG : On Start");
		
	}

	public void onTestFailedButWithinSuccessPercentage(ITestResult arg0) {
		// TODO Auto-generated method stub
		
	}

	public void onTestFailure(ITestResult arg0) {
		LogReport.error("TESTNG : On Test Failure : " + arg0.getName());
		
	}

	public void onTestSkipped(ITestResult arg0) {
		LogReport.info("TESTNG : On Test Skipped : " + arg0.getName());
		
	}

	public void onTestStart(ITestResult arg0) {
		LogReport.info("TESTNG : On Test Start : " + arg0.getName());
		
	}

	public void onTestSuccess(ITestResult arg0) {
		LogReport.info("TESTNG : On Test Success : " + arg0.getName() );
		
	}

}
