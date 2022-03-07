package com.test;

//import nothing.LoggerA;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.openqa.selenium.ie.InternetExplorerDriver;
import org.testng.ITestResult;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.BeforeSuite;
import org.testng.annotations.BeforeTest;
import org.testng.annotations.Optional;
import org.testng.annotations.Parameters;

public class BaseRepeat {

	
	protected WebDriver driver;
	protected String appURL;
	
	@BeforeTest
	@Parameters("appURL")
	public void setEnv(@Optional("http://newtours.demoaut.com/mercuryregister.php") String appURL) {
		this.appURL = appURL;
		System.out.println("Successfully set the value of appURL");
	}
	
	@BeforeMethod()
	@Parameters("browser")	
	public void LaunchBrowser(@Optional("FF") String browser) {
		
		if (browser.equalsIgnoreCase("Chrome")) {
		System.setProperty("webdriver.chrome.driver", "D:\\WS\\SikuliQAR421_Catia_U2I\\win_b64\\resources\\testfw\\Tools\\chromedriver.exe");
		// here instead of D:\Automation\Selenium\chromedriver_win32 must write as above given
		driver = new ChromeDriver();
		}
		
		else if (browser.equalsIgnoreCase("FF")) {  
			driver = new FirefoxDriver();
			}
		else {
			System.setProperty("webdriver.ie.driver", "D:/Automation/Selenium/IEDriverServer_x64_2.45.0/IEDriverServer.exe");

			driver = new InternetExplorerDriver();
		}
		
	}
	
	
	// testng handles ITestResult, it injects this object as param in this after method function
	@AfterMethod
	public void CloseBrowser(ITestResult result) {
		if (result.isSuccess()) {
			System.out.println("Test is successful");
		} else {
			System.out.println("Test is FAILED. Capturing screenshot");
		}
		driver.close();
		driver.quit();
	}
	
	
	public static void maximiseBrowser(WebDriver driver ) {
		driver.manage().window().maximize();  // Maximize the window
	//	LoggerA.info("Broser is maximised");
	}
	
	
	public static void closeBrowser( WebDriver driver) {
		driver.close();
	//	LoggerA.info("Browser is closed");
	}
	

}

