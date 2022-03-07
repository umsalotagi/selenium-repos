package com.pageObject;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.Select;

import com.dataObject.RegistrationData;

public class NewRegistration {
	
	private WebDriver driver ;
	
	public NewRegistration( WebDriver driver){
		this.driver = driver;
	}
	
	// actions and function from particular page is collected here
	/*
	 * Hide your implementation details. 
	 * Test should not do operation on page.
	 * single responsibility . Test object should do test,not operation
	 * assertion should be done only in test , not in page object
	 * Return new Page object for new page
	 */
	
	
	
	
	/*
	 * TESTNG
	 * 
	 * TestNG is a testing framework inspired from JUnit and NUnit, but introducing some new functionalities that make it more powerful and easier to use.
	 * TestNG is an open source automated testing framework; where NG means NextGeneration
	 * 
	 * Test runs sequentially, in alphabetical order, one after another.
	 * 
   <suite name = "Sample test Suite">
	   <test name = "Sample test">
	   <parameter name="browser" value="Chrome"></parameter>
	      <classes>
	         <class name = "SampleTest" />
	      </classes>
	      <groups>
	         <run>
	            <include name = "functest" />
	         </run>
	      </groups>
	   </test>
	</suite>

To handle above we have, @BeforeSuite, @BeforeTest, @BeforeClass, @BeforeMethod, @Test, @AfterMethod, @BeforeMethod, @Test, @AfterMethod, @AfterClass, @AfterTest, @AfterSuite


@Test(enabled = false, groups = { "functest", "checkintest", "init" }, dependsOnMethods="testOne", dataProvider = "test1")
@Parameters("url")
@Test (dataProvider = "regData" , dataProviderClass = RegistrationData.class)   we need to provide class when regData is not in same class of test case.

@DataProvider(name = "test1")

@Test(expectedExceptions = ArithmeticException.class, dependsOnGroups = { "init.*" }, alwaysRun=true)

enabled - skip the test
groups - grouping the test
dependsOnMethods - when dependent method runs completely and successful and then this test is run otherwise skipped
dependsOnGroups - 
alwaysRun - no matter dependent method runs or not, this test always get executed
dataProvider - from which data provider data is collected for data driven testing, test is run multiple times
expectedExceptions - thrown exception is checked. ( we can say it as assert for exception)

@DataProvider - non test function which returns two dimenstion array. { {data, for, one test}, {data, for, second, test} }
@Parameters - test which needs param for their run

 You can execute your existing JUnit test cases using TestNG. - <test name = "JUnitTests" junit="true">
	 */
	
	
	public NewRegistration enterFirstName(String firstName) {
		driver.findElement(By.name("firstName")).sendKeys(firstName);
		return this;
	}
	
	public NewRegistration enterLastName(String LastName) {
		driver.findElement(By.name("lastName")).sendKeys(LastName);
		return this;
	}
	
	public NewRegistration enterPhone(String phone) {
		driver.findElement(By.name("phone")).sendKeys(phone);
		return this;
	}
	
	
	public NewRegistration enterUserName(String userName) {
		driver.findElement(By.name("userName")).sendKeys(userName);
		return this;
	}
	
	
	public NewRegistration enterCountry(String country) {
		new Select(driver.findElement(By.name("country"))).selectByVisibleText(country);
		return this;
	}
	
	
	public NewRegistration enterEmail(String email) {
		driver.findElement(By.name("email")).sendKeys(email);
		return this;
	}
	
	public NewRegistration enterPassword(String password) {
		driver.findElement(By.name("password")).sendKeys(password);
		return this;
	}
	
	public NewRegistration enterConfirmPassword(String password) {
		driver.findElement(By.name("confirmPassword")).sendKeys(password);
		return this;
	}
	
	public AccountCreationPage clickRegister() {
		driver.findElement(By.name("register")).click();
		return new AccountCreationPage(driver);
	}
	
	
	
	
	public AccountCreationPage registerNewUser(RegistrationData registrationData) {
		
		return enterFirstName(registrationData.getFirstName()).enterLastName(registrationData.getLastName()).
				enterPhone(registrationData.getPhone()).enterUserName(registrationData.getUserName()).
				enterCountry(registrationData.getCountry()).enterEmail(registrationData.getCountry()).
				enterPassword(registrationData.getPassword()).
				enterConfirmPassword(registrationData.getPassword()).clickRegister();

	}
	
	
	
	
	
	
	


}
