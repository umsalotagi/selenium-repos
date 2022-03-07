package PageFactory;

import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.GregorianCalendar;
import java.util.Random;

import org.apache.commons.io.FileUtils;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.openqa.selenium.ie.InternetExplorerDriver;
import org.testng.ITestResult;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Optional;
import org.testng.annotations.Parameters;

public class BaseRepeat6 {
	
	

	protected WebDriver driver;
	
	@BeforeMethod()
	@Parameters("browser")
	
	public void LaunchBrowser(@Optional("FF") String browser) {
		
		
		if (browser.equalsIgnoreCase("Chrome")) {
		System.setProperty("webdriver.chrome.driver", "D:/Automation/Selenium/chromedriver_win32/chromedriver.exe");
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
	
	@AfterMethod
	public void CloseBrowser(ITestResult result) throws IOException {
		
//		if (!result.isSuccess()) {
//			File imagefile =  ((TakesScreenshot) driver).getScreenshotAs(OutputType.FILE);
//			String failueImageFileName = result.getMethod().getMethodName() + new SimpleDateFormat("MM-dd-yyyy"
//					+ "_HH-ss").format(new GregorianCalendar().getTime()) + ".png";
//			
//			File failureImageFile = new File(failueImageFileName);
//			FileUtils.moveFile(imagefile, failureImageFile);
//			
//		}
		
		
		
//		
		Random randomGenerator = new Random();
		int randomInt = randomGenerator.nextInt();
	
			File imagefile =  ((TakesScreenshot) driver).getScreenshotAs(OutputType.FILE);
			String failueImageFileName = result.getMethod().getMethodName() + randomInt + "__" + new SimpleDateFormat("MM-dd-yyyy"
					+ "_HH-ss").format(new GregorianCalendar().getTime()) + ".png";
			
			File failureImageFile = new File(failueImageFileName);
			FileUtils.moveFile(imagefile, failureImageFile);
			
		
		
		driver.close();
		driver.quit();
	} 

}
