package com.dsone.example;


import java.lang.reflect.Method;
import java.util.ArrayList;

import org.openqa.selenium.WebDriver;

import utility.DataReader;

public class ExampleOne {

	
	public static void main(String[] args)  {
		WebDriver driver = null;
		DataReader.path = "D:\\Automation\\Selenium\\InitialData.txt";
		
		
		String browserClass = "utility.Browser";
		String setBrowserMethod = "setBowser";
		
		//Class class;
		Method method = null;
		Object Obj = null;
		Method methodCloseBrowser = null;
		Method methodMaxBrowser = null;
		Method methodTemp = null;
		
		Class[] parameters = new Class[2];
		parameters[0] = WebDriver.class;
		parameters[1] = String.class;
		
		ArrayList<Class> parameters2 = new ArrayList<Class>();
		parameters2.add(WebDriver.class);
		parameters2.add(String.class);
		
		Class[] parameters3 = new Class[parameters2.size()];
		
		int para = 2;
		Class[] parameters4 = new Class[para];
		parameters4[0] = WebDriver.class;
		parameters4[1] = String.class;
		
		try {
			Class<?> cls = Class.forName(browserClass);
			Obj = cls.newInstance();

			method = cls.getMethod(setBrowserMethod, parameters );
		//	method = cls.getMethod(setBrowserMethod, parameters2.toArray(parameters3));
		//	method = cls.getMethod(setBrowserMethod, parameters4 );
			methodMaxBrowser = cls.getMethod("maximiseBrowser", new Class[] {WebDriver.class} );
			methodCloseBrowser = cls.getMethod("closeBrowser", WebDriver.class);
			methodTemp = cls.getMethod("tempMethod" );  // method without any parameter
			
		} catch (Exception e) {
			System.out.println("exception is here");
		}
		
		
		Object OrangeHrmsObj = null;
		Method loginMethod = null;
		
		try {
			Class<?> cls = Class.forName("function.OrangeHrms");
			OrangeHrmsObj = cls.newInstance();
			loginMethod = cls.getMethod("Login", new Class[] {WebDriver.class ,String.class,String.class}  );
			
		} catch (Exception e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		
		
		System.out.println("done here");
		
		
		try {
			driver = (WebDriver) method.invoke(Obj, driver , "Firefox");
			methodMaxBrowser.invoke(Obj, driver);
			loginMethod.invoke(OrangeHrmsObj, driver, "Admin" , "admin");
			methodCloseBrowser.invoke(Obj, driver);
			methodTemp.invoke(Obj );
			
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		
		}
		
		
		
		
		
	//	driver = Browser.setBowser( DataReader.getData("Browser"));
	//	Browser.maximiseBrowser(driver);
		

	//	OrangeHrms.Login(driver, DataReader.getData("LoginID"), DataReader.getData("Password"));
		
	//	Browser.closeBrowser(driver);
		
		
		
		
		
		/*
		
//		driver.manage().timeouts().pageLoadTimeout(5, TimeUnit.SECONDS);
		driver.findElement(By.className("firstLevelMenu")).click();
		driver.findElement(By.id("menu_admin_Qualifications")).click();
		driver.findElement(By.id("menu_admin_viewEducation")).click();
		
	//	new Select(driver.findElement(By.id("recordsListTable"))).selectByValue("2");
	//	new Select(driver.findElement(By.cssSelector("table[id='recordsListTable']"))).selectByValue("2");
		
		driver.findElement(By.cssSelector("input[value='2']")).click();
		
		driver.findElement(By.id("btnAdd")).click();
		
		*/
		
		

	}

}
