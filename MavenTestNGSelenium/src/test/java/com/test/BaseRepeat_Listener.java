package com.test;

import java.net.URL;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.events.EventFiringWebDriver;
import org.testng.ITestResult;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.BeforeTest;
import org.testng.annotations.Optional;
import org.testng.annotations.Parameters;

public class BaseRepeat_Listener {
	
	protected WebDriver driver;
	protected String url;
	
	@BeforeMethod
	@Parameters("browser")
	public void login(@Optional("chrome") String browser) {
		LogReport.info("inside login broser used " + browser);
		if (browser.equalsIgnoreCase("ff")) {
			LogReport.info("Firefox browser");
			driver = null;
		} else if (browser.equalsIgnoreCase("chrome")){
			LogReport.info("chrome browser");
			System.setProperty("webdriver.chrome.driver", "D:\\WS\\SikuliQAR421_Catia_U2I\\win_b64\\resources\\testfw\\Tools\\chromedriver.exe");
			// here instead of D:\Automation\Selenium\chromedriver_win32 must write as above given
			driver = new ChromeDriver();
		}
		
		EventFiringWebDriver d = new EventFiringWebDriver(driver);
		MyWebDriverListener listener = new MyWebDriverListener();
		d.register(listener);
		driver =d;
		driver.get(url);
	}
	
	@AfterMethod
	public void tearDown(ITestResult result) {
		LogReport.info("closing driver");
		if (result.isSuccess()) {
			LogReport.info("This is success");
		} else {
			LogReport.error("This is failure");
		}
		driver.close();
		driver.quit();
	}
	
	@BeforeTest
	@Parameters("url")
	public void start(@Optional("http://newtours.demoaut.com/mercuryregister.php") String url) {
		LogReport.info("This is url " + url);
		this.url = url;
	}

}
