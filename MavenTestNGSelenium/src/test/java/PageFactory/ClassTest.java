package PageFactory;

import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.support.PageFactory;
import org.testng.annotations.Test;



public class ClassTest extends BaseRepeat6 {
	
	

	@Test (dataProvider = "regData" , dataProviderClass = RegistrationData.class)
	public  void testRegistrationNew( String firstName, String lastName, String phone,
			String userName, String country, String email,  String password, String confirmPassword)  
		{
		
		
		RegistrationData registrationData = new RegistrationData();
		registrationData.setFirstName (firstName);
		registrationData.setLastName(lastName);
		registrationData.setPhone(phone);
		registrationData.setUserName(userName);
		registrationData.setCountry(country);
		registrationData.setEmail(email);
		registrationData.setPassword(password);
		registrationData.setConfirmPassword(confirmPassword);
		
		RegistrationPage registration = PageFactory.initElements(driver, RegistrationPage.class); 
							// here we are initializing the WebElement through PageFactory.
		// RegistrationPage registration = new RegistrationPage(driver); 
		
		driver.get("http://newtours.demoaut.com/mercuryregister.php"); 
		
		registration.registerNewUser(registrationData); 
			
		assert driver.findElement(By.tagName("body")).getText().contains("Thank you for registering. You"+
										" may now sign-in using the user name and password you've just entered.");
		}
	
		
	@Test
	public void TestJScriptExecutor() throws InterruptedException {
			driver.get("http://newtours.demoaut.com/mercuryregister.php");
			((JavascriptExecutor) driver).executeScript("document.getElementsByName('firstName')[0].value='Java Script'", "d");
//			((JavascriptExecutor) driver).execteScript("document.getElementsByName('firstName')[0].value='Deepika'");
			// , "d" does not have any meaning .... it is passed because it ia need.
		}
		

	

}
