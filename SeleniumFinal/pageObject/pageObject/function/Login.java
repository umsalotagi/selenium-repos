package pageObject.function;

import log4j.log.LoggerA;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

public class Login {
	
	// This is page object model. Here we have kept all the objects that are required in up in class.
	// this is useful for maintaining the objects of page. If any objects are changed then
	// that objects are need to change in that page only
	// and that object are need to changed and found in upper part of class so
	// we does not need to go in every function and make changes. we just make changes here in upper part.
	
	By txt_username = By.name("txtUsername"); // objects.. maintenance is easy
	By txt_password = By.name("txtPassword");
	By btn_login = By.id("btnLogin");
	private WebDriver driver;
	
	
	public Login ( WebDriver driver) {
		this.driver = driver;
	}
	
	public WebElement txtUsername () {
		return driver.findElement(txt_username);
	}
	
	public WebElement txtPassword() {
		return driver.findElement(txt_password);
	}
	
	public WebElement btnLogin() {
		return driver.findElement(btn_login);
		
	}
	
	public void loginHRM ( String user, String pwd) {
		this.txtUsername().sendKeys(user);
		this.txtPassword().sendKeys(pwd);
		this.btnLogin().click();
		LoggerA.info("Login is successful");
	}

}
