package com.test;

import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;

import org.testng.Reporter;
import org.testng.annotations.Listeners;
import org.testng.annotations.Test;

import junit.framework.Assert;

//@Listeners(com.test.MyTestNGListener.class)
public class TestNGBasics {
	
	@Test
	public void dtestOne() {
		Calendar cal = Calendar.getInstance();
	    Date date=cal.getTime();
	    DateFormat dateFormat = new SimpleDateFormat("HH:mm:ss");
	    String formattedDate=dateFormat.format(date);
	    LogReport.info("Testing d start");
	    LogReport.error("Current time of the day using Calendar - 24 hour format: "+ formattedDate);
	    
	    
		try {
			Thread.sleep(4000);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		LogReport.info("Testing d one #DONE");
		assert true==false;
	}
	
	@Test
	public void etestOne() {
		Calendar cal = Calendar.getInstance();
	    Date date=cal.getTime();
	    DateFormat dateFormat = new SimpleDateFormat("HH:mm:ss");
	    String formattedDate=dateFormat.format(date);
	    System.out.println("Current time of the day using Calendar - 24 hour format: "+ formattedDate);
	    
	    LogReport.info("Testing e one");
		try {
			Thread.sleep(4000);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		LogReport.info("Testing e one.. #DONE");
	}
	
	@Test
	public void ftestOne() {
		Calendar cal = Calendar.getInstance();
	    Date date=cal.getTime();
	    DateFormat dateFormat = new SimpleDateFormat("HH:mm:ss");
	    String formattedDate=dateFormat.format(date);
	    LogReport.info("Current time of the day using Calendar - 24 hour format: "+ formattedDate);
	    
	    
	    LogReport.info("Testing f one");
		try {
			Thread.sleep(4000);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		LogReport.info("Testing f one # DONE");
	}
	
	@Test(testName="This is First Test")
	public void atestOne() {
		LogReport.info("Testing a one");
		Assert.assertFalse(false);
	}
	
	@Test
	public void btestOne() {
		Calendar cal = Calendar.getInstance();
	    Date date=cal.getTime();
	    DateFormat dateFormat = new SimpleDateFormat("HH:mm:ss");
	    String formattedDate=dateFormat.format(date);
	    LogReport.info("Current time of the day using Calendar - 24 hour format: "+ formattedDate);
	    
	    LogReport.info("Testing b one");
	}
	
	@Test
	public void ctestOne() {
		LogReport.info("Testing c one");
	}
	
	@Test (dependsOnMethods="ftestOne")
	public void g_dependsOnFPass_ShouldFail() {
		LogReport.error("This is F method");
		int a = 2+2;
		Assert.assertEquals(10, a);
	}
	
	@Test (dependsOnMethods="g_dependsOnFPass_ShouldFail")
	public void h_dependsOnFail() {
		LogReport.info("This is one method");
		int a = 2+2;
		Assert.assertEquals(4, a);
	}
	
	@Test(expectedExceptions=NullPointerException.class)
	public void i_exceptionTest() {
		LogReport.info("This is one method");
		ArrayList<String> ll = null;
		ll.add("This is good");
	}
	
	@Test (dependsOnMethods="g_dependsOnFPass_ShouldFail", alwaysRun=true)
	public void j_dependsOnFail_alwasyRun() {
		LogReport.info("This is one method");
		String k = "22";
		Assert.assertNotNull(k);
	}
	
	@Test (enabled=false)
	public void k_notEnabledTest() {
		LogReport.info("This is one method");
		String k = "22";
		Assert.assertNotNull(k);
	}
	
	@Test (enabled=true)
	public void l_enabledTest() {
		LogReport.info("This is one method");
		String k = "22";
		Assert.assertNotNull(k);
	}

	
	

}
