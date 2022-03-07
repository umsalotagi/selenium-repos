package function;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

public class OrangeHrms {
	
	
	public static void Login ( WebDriver driver , String loginId , String password) {
	//	String ttk = "By.name("txtUsername")" ; 
		
		driver.get("http://opensource.demo.orangehrm.com/");
		WebElement userName = driver.findElement(By.name("txtUsername"));
		userName.sendKeys(loginId);
		
		// we will directly do type password
		driver.findElement(By.name("txtPassword")).sendKeys(password);
		driver.findElement(By.id("btnLogin")).click();
	}

}
