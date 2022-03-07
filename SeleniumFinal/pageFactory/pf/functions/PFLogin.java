package pf.functions;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.PageFactory;

public class PFLogin extends MakeSleep{
	
	
//	By txt_username;
//	By txt_password;
//	By btn_login;
	private WebDriver driver; // we need this in here
	
	@FindBy ( name = "txtUsername")
	WebElement txt_Username;
	
	@FindBy ( name = "txtPassword")
	WebElement txt_Password;
	
	@FindBy (id = "btnLogin")
	WebElement btn_Login;
	
	
	
	public PFLogin ( WebDriver driver) {
		this.driver = driver;  // we need to keep this also
		PageFactory.initElements(driver, this);
	}
	
	/*
	public WebElement txtUsername () {
		return driver.findElement(By.name("txtUsername"));
	}
	
	public WebElement txtPassword() {
		return driver.findElement(By.name("txtPassword"));
	}
	
	public WebElement btnLogin() {
		return driver.findElement(By.id("btnLogin"));
	}*/
	
	public PFLogin setUserName( String userName) {
		txt_Username.sendKeys(userName);
		return this;
	}
	
	public PFLogin setPassword (String password) {
		txt_Password.sendKeys(password);
		return this;
	}
	
	public PFMainPage clickbtn_Login () {
		btn_Login.click();
		return new PFMainPage(driver);  // This must return the page object of different page which will be redirected 
								// after clicking the login button.
	}
	
	public PFMainPage loginHRM ( String user, String pwd) {
		return setUserName("Admin").setPassword("admin").clickbtn_Login();
	}


}
