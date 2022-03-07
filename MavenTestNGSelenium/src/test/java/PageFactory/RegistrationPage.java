package PageFactory;


import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.GregorianCalendar;

import org.apache.commons.io.FileUtils;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.CacheLookup;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.PageFactory;
import org.openqa.selenium.support.ui.Select;

public class RegistrationPage {
private WebDriver driver ;
	
	public RegistrationPage( WebDriver driver){
		this.driver = driver;
	}
	
	
	@CacheLookup
	@FindBy (name = "firstName")
	WebElement firstNameTextbox;
	
	@CacheLookup
	@FindBy (name = "lastName")
	WebElement lastNameTextbox;
	
	@CacheLookup
	@FindBy (name = "phone")
	WebElement phoneTextbox;
	
	@CacheLookup
	@FindBy (name = "userName")
	WebElement userNameTextbox;
	
	@CacheLookup
	@FindBy (name = "country")
	WebElement countryDropdown;
	
	@CacheLookup
	@FindBy (name = "email")
	WebElement emailTextbox;
	
	@CacheLookup
	@FindBy (name = "password")
	WebElement passwordTextbox;
	
	@CacheLookup
	@FindBy (name = "confirmPassword")
	WebElement confirmPasswordTextbox;
	
	@CacheLookup
	@FindBy (name = "register")
	WebElement registerButton;
	
	
	public RegistrationPage captureImage() {
		
		
		File imagefile =  ((TakesScreenshot) driver).getScreenshotAs(OutputType.FILE);
		String failueImageFileName = new SimpleDateFormat("MM-dd-yyyy"
				+ "_HH-ss").format(new GregorianCalendar().getTime()) + ".png";
		
		File failureImageFile = new File(failueImageFileName);
		try {
			FileUtils.moveFile(imagefile, failureImageFile);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return this;
	}



	public RegistrationPage enterFirstName(String firstName) {
		firstNameTextbox.sendKeys(firstName);
		return this;
	}
	
	public RegistrationPage enterLastName(String LastName) {
		lastNameTextbox.sendKeys(LastName);
		return this;
	}
	
	public RegistrationPage enterPhone(String phone) {
		phoneTextbox.sendKeys(phone);
		return this;
	}
	
	
	public RegistrationPage enterUserName(String userName) {
		userNameTextbox.sendKeys(userName);
		return this;
	}
	
	
	public RegistrationPage enterCountry(String country) {
		new Select(countryDropdown).selectByVisibleText(country);
		return this;
	}
	
	
	public RegistrationPage enterEmail(String email) {
		emailTextbox.sendKeys(email);
		return this;
	}
	
	public RegistrationPage enterPassword(String password) {
		passwordTextbox.sendKeys(password);
		return this;
	}
	
	public RegistrationPage enterConfirmPassword(String password) {
		confirmPasswordTextbox.sendKeys(password);
		return this;
	}
	
	public AccountCreationPage clickRegister() {
		registerButton.click();
		return PageFactory.initElements(driver, AccountCreationPage.class);
		// here while returning the new class object we are returning it by PageFactory 
		// by initializing its WebElemets.

	}
	
	
	
	
	public AccountCreationPage registerNewUser(RegistrationData registrationData) {
		

			return enterFirstName(registrationData.getFirstName()).enterLastName(registrationData.getLastName()).
					enterPhone(registrationData.getPhone()).enterUserName(registrationData.getUserName()).
					enterCountry(registrationData.getCountry()).enterEmail(registrationData.getCountry()).
					enterPassword(registrationData.getPassword()).
					enterConfirmPassword(registrationData.getPassword()).clickRegister();
		
	}
	
	
	
	
	

}
