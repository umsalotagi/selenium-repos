package pageObject.utility;
import log4j.log.LoggerA;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.firefox.FirefoxDriver;

public class pageBrowser {

	
	
	public static WebDriver setBowser( WebDriver driver, String browser) {
		
		LoggerA.prerequisite();
		
		if ( browser.equals("Firefox")) {
			driver = new FirefoxDriver();	
		}
		else if (browser.equals("Chrome")) {
			System.setProperty("webdriver.chrome.driver", "D:/Automation/Selenium/chromedriver_win32/chromedriver.exe");
			driver = new ChromeDriver();	
		}
		LoggerA.info("Broser is set");
			
		return driver;		
	}
	
	
	public static void maximiseBrowser(WebDriver driver ) {
		driver.manage().window().maximize();  // Maximize the window
		LoggerA.info("Broser is maximised");
	}
	
	
	public static void closeBrowser( WebDriver driver) {
		driver.close();
		LoggerA.info("Broser is closed");
	}
	
	public static void tempMethod () {
		System.out.println("temporary");
	}

}

