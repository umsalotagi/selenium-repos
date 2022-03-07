package com.test;

import org.testng.annotations.Test;

import junit.framework.Assert;

public class VerifyVsValidate {
	
	@Test
	public  void testRegistrationNONDataDriven() {
		int x = 5;
		Assert.assertEquals(5, x);
	}
	
	@Test
	public void one() {
		try {
			int x = 6;
			Assert.assertEquals(5, x);
		} catch (Error e) {
			e.toString();
			LogReport.error("This is error");
		}
		LogReport.info("This is not");
		System.out.println("proceededdddd");
	}
	
	@Test
	public void two() {
		int x = 6;
		Assert.assertEquals(5, x);
		LogReport.info("This is not");
		System.out.println("proceededdddd");
	}

}
