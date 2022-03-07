package com.test;

import org.testng.annotations.Test;

// https://stackoverflow.com/questions/26632241/priority-in-testng-with-multiple-classes

public class PriorityTest {
	
	@Test(priority=4) // always default priority is 0
	public void test0() {
		PriorityTest.sleep();
		LogReport.info("This is test0 p4");
	}
	
	public static void sleep() {
		try {
			Thread.sleep(2000);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	@Test(priority=3) // always default priority is 0
	public void test1() {
		PriorityTest.sleep();
		LogReport.info("This is test1 p3");
	}
	
	@Test(priority=2) // always default priority is 0
	public void test2() {
		PriorityTest.sleep();
		LogReport.info("This is test2 p2");
	}
	
	@Test(priority=1) // always default priority is 0
	public void test3() {
		PriorityTest.sleep();
		LogReport.info("This is test3 p1");
	}
	
	@Test(priority=0) // always default priority is 0
	public void test4() {
		PriorityTest.sleep();
		LogReport.info("This is test4 p0");
	}

}
