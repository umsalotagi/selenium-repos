package xpath;

import java.awt.AWTException;
import java.awt.Robot;
import java.awt.event.InputEvent;
import java.util.concurrent.TimeUnit;

import org.openqa.selenium.By;
import org.openqa.selenium.Point;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

public class LearnActions {
	
	public static void sleeping ( int millisec) {
		try {
			Thread.sleep(millisec);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	
	public static boolean exists( WebDriver driver ) { //, WebElement element ) {
		Actions actions = new Actions(driver);
		actions.moveToElement(driver.findElement(By.className("compass-small")));
		driver.manage().timeouts().implicitlyWait(1, TimeUnit.SECONDS);
		
		
		while ( true) {
			actions.moveByOffset(-3, 0).build().perform();
			System.out.println("done44");
	//		if (!driver.findElements(By.className("compass-small-over west")).isEmpty()) {
	//			driver.findElement(By.className("compass-small-over west")).click();
	//			return true;
	//		}	
			
			if (!driver.findElements(By.xpath("//div[@class = 'compass-small-over west']")).isEmpty()) {
				System.out.println("extreme");
				WebElement e = driver.findElement(By.xpath("//div[@class = 'compass-small-over west']"));
				actions.click(e);
				Point p = e.getLocation();
				
				try {
					Robot r = new Robot();
					r.mouseMove(p.getX(), p.getY()); 
					System.out.println(p.getX() + "  " +  p.getY()  + " " + p.x + " " + p.y);
					r.mousePress(InputEvent.BUTTON1_DOWN_MASK);
					r.delay(10);
					r.mouseRelease(InputEvent.BUTTON1_DOWN_MASK);
					System.out.println("gg");
				} catch (AWTException et) {
					// TODO Auto-generated catch block
					et.printStackTrace();
				}
				actions.click(driver.findElement(By.xpath("//div[@class = 'compass-small-over west']")));
				driver.manage().timeouts().implicitlyWait(15, TimeUnit.SECONDS);
				return true;
				
			}
		}
		
	//	while (ExpectedConditions.presenceOfElementLocated(By.className("compass-small-over west")))
			
	
	}
	
	public static void main(String[] args) {
		
		System.setProperty("webdriver.chrome.driver", "D:/Automation/Selenium/chromedriver_win32/chromedriver.exe");
		WebDriver driver = new ChromeDriver();
	//	WebDriver driver = new FirefoxDriver();
		
		driver.manage().timeouts().implicitlyWait(15, TimeUnit.SECONDS);
		// An implicit wait is to tell WebDriver to poll the DOM for a certain amount of time
		//when trying to find an element or elements if they are not immediately available.
		
		driver.get("http://vdevpril606am:10490/ematrix/common/emxNavigator.jsp?isPopup=true");
		driver.manage().window().maximize();  // Maximize the window
	
		
		
		
		driver.findElement(By.name("login_name")).sendKeys("wyj"); /// wyj
		driver.findElement(By.name("login_password")).sendKeys("wyj");
		driver.findElement(By.className("btn")).click();
		
		
		(new WebDriverWait(driver, 30))
		  .until(ExpectedConditions.presenceOfElementLocated(By.id("mydeskpanel")));
		// this is to make wait until element with id "mydeskpanel" becomes available.
		//before switching to frame we need to wait until frame is loaded. generally frame becomes visible ..
		// ..if one of element of parent becomes visible. so making it condition.
		
//		if (!driver.findElements(By.className("ds-coachmark-close")).isEmpty() ) { // It may implicitly waiting for 15 sec
//			System.out.println("is present");
//			driver.findElement(By.className("ds-coachmark-close")).click();
//		}
		
		try {
			driver.findElement(By.className("ds-coachmark-close")).click();
			
		}
		catch (Exception e) {
			System.out.println("Welcome screen unavaialable");
		}
		
		System.out.println("done");
		
		
		LearnActions.exists(driver);
		
		System.out.println("done3");
		
	}

}
