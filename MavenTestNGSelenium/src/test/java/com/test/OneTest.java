package com.test;

import org.openqa.selenium.By;
import org.testng.annotations.Test;

import com.dataObject.RegistrationData;
import com.pageObject.NewRegistration;


public class OneTest extends BaseRepeat{
	
	// here we cannot run methods in parallel, because of BaseReapet
	// BaseRepeat holds value of driver for this entire test class.
	// means entire test class share same value of driver and url, which result inconsistency when test run in parallel
	
	// we hard code data in function itself when we don't have any plans to use that function with parameters.
	@Test
	public  void testRegistrationNONDataDriven()  
		{		
		RegistrationData registrationData = new RegistrationData();
		registrationData.setFirstName ("first");
		registrationData.setLastName("second");
		registrationData.setPhone("58696");
		registrationData.setUserName("have");
		registrationData.setCountry("INDIA");
		registrationData.setEmail("one#gmail.com");
		registrationData.setPassword("%eet");
		registrationData.setConfirmPassword("%eet");
		
		NewRegistration registration = new NewRegistration(driver);  // here we launch the chrome/FF
		
		System.out.println("appURL");
		System.out.println(appURL);
		driver.get("http://newtours.demoaut.com/mercuryregister.php"); // here we go to desired site
		
		registration.registerNewUser(registrationData); 
			
		assert driver.findElement(By.tagName("body")).getText().contains("Thank you for registering. You"+
										" may now sign-in using the user name and password you've just entered.");
		}
	
	
	@Test(dataProvider="regData", dataProviderClass=RegistrationData.class, dependsOnMethods="testRegistrationNONDataDriven")
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
		
		// driver and appURL values are taken from parent class
		NewRegistration registration = new NewRegistration(driver);  // here we launch the chrome/FF
		System.out.println("appURL");
		System.out.println(appURL);
		//driver.get(appURL); // here we go to desired site
		driver.get("http://newtours.demoaut.com/mercuryregister.php"); // here we go to desired site
		
		registration.registerNewUser(registrationData); 
			
		assert driver.findElement(By.tagName("body")).getText().contains("Thank you for registering. You"+
										" may now sign-in using the user name and password you've just entered.");
		}
	
}
