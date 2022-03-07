package pageObject.test;

import org.openqa.selenium.WebDriver;

import pageObject.function.Login;
import pageObject.utility.pageBrowser;
import pageObject.utility.pageDataReader;

public class testOne {
	
	
	public static void main(String[] args) {
		
		
		WebDriver driver=null;
		pageDataReader.path = "D:\\Automation\\Selenium\\InitialData.txt";
		driver = pageBrowser.setBowser(driver, pageDataReader.getData("Browser"));
		
		driver.get(pageDataReader.getData("url"));
		
		Login login = new Login(driver);		
		login.txtUsername().sendKeys(pageDataReader.getData("LoginID"));
		login.txtPassword().sendKeys(pageDataReader.getData("Password"));
		login.btnLogin().click();
		
		pageBrowser.closeBrowser(driver);
		
	
	}
	

}
