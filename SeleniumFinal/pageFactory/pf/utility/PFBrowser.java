package pf.utility;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.firefox.FirefoxDriver;

public class PFBrowser {
	
public static WebDriver setBowser( WebDriver driver, String browser) {
		
		if ( browser.equals("Firefox")) {
			driver = new FirefoxDriver();	
		}
		else if (browser.equals("Chrome")) {
			System.setProperty("webdriver.chrome.driver", "D:/Automation/Selenium/chromedriver_win32/chromedriver.exe");
			driver = new ChromeDriver();	
		}
			
		return driver;		
	}
	
	
	public static void maximiseBrowser(WebDriver driver ) {
		driver.manage().window().maximize();  // Maximize the window
	}
	
	
	public static void closeBrowser( WebDriver driver) {
		driver.close();
	}
	
	public static void tempMethod () {
		System.out.println("temporary");
	}

}
