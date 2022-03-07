package xpath;

import java.util.Set;
import java.util.concurrent.TimeUnit;

import org.openqa.selenium.Alert;
import org.openqa.selenium.By;
import org.openqa.selenium.Cookie;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

public class locator {
	
	public static void sleeping ( int millisec) {
		try {
			Thread.sleep(millisec);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
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
	
		
		
		
		driver.findElement(By.name("login_name")).sendKeys("u2i"); /// wyj
		driver.findElement(By.name("login_password")).sendKeys("u2i");
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
		
		
		Actions actions = new Actions(driver);
		actions.moveToElement(driver.findElement(By.className("compass-small")));
		
		actions.build().perform();
		
		sleeping(5000);
		
		
		
		
		driver.switchTo().frame("content").switchTo().frame("frameDashboard").switchTo().frame("portalDisplay")
		.switchTo().frame("APPDashboardUserNewDocs");
		
	//	driver.switchTo().frame("APPDashboardUserNewDocs");
		
		System.out.println("done2");
		
//		driver.manage().timeouts().implicitlyWait(15, TimeUnit.SECONDS);
//		(new WebDriverWait(driver, 30))
//		  .until(ExpectedConditions.presenceOfElementLocated(By.id("rmbrow-0,0")));
		
		driver.findElement(By.id("rmbrow-0,0")).click();
		System.out.println("done3");
		driver.findElement(By.xpath("//div[@id = 'pageHeadDiv']//*[@title='Launch']")).click();
	//	driver.findElement(By.)
		//	To switch latest window opened use below code:
		System.out.println("Title of the page before - switchingTo: " + driver.getTitle());
		String parentWindow = driver.getWindowHandle();
		
		for(String winHandle : driver.getWindowHandles()){
			driver.switchTo().window(winHandle);
			System.out.println(winHandle);
			if (driver.getTitle().equals("ENOVIA"))
				break;
		}
		
		
		System.out.println("Title of the page afetr - switchingTo: " + driver.getTitle());
		
		driver.switchTo().frame("content");
		
	/*	
		try {
			Thread.sleep(8000);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		Alert alert = driver.switchTo().alert();  // this alert is not recognised by selenium
		alert.dismiss();
		*/
		
		driver.findElement(By.name("emxTableRowIdActual")).click();
		driver.close();
		driver.switchTo().window(parentWindow);
//		sleeping(3000);
		driver.navigate().to("https://translate.google.co.in/");
//		sleeping(3000);
		driver.findElement(By.id("source")).sendKeys("Happy");
//		driver.findElement(By.linkText("Spanish")).click();
//		sleeping(3000);
		driver.findElement(By.id("gt-submit")).click();
//		sleeping(3000);
		driver.navigate().back();
//		sleeping(3000);
		driver.navigate().back();
		driver.navigate().forward();
		System.out.println("done done");
		
		Cookie cookyb = new Cookie("kay re baba", "value tar dee ki");
	//	driver.manage().addCookie(cookyb);
		
		driver.manage().deleteAllCookies();
		Set<Cookie> allCookies = driver.manage().getCookies();
		for (Cookie loadedCookie : allCookies) {
		    System.out.println(String.format("%s -> %s", loadedCookie.getName(), loadedCookie.getValue()));
		}
		
		WebDriverWait waited = new WebDriverWait(driver, 12);
		waited.until(ExpectedConditions.elementToBeClickable(By.className("")));
		
		//driver.switchTo().defaultContent(); // used only for iframe
	//	driver.switchTo().
		
		
	}

}
