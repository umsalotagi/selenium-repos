package pf.test;

import org.openqa.selenium.WebDriver;

import pf.functions.PFLogin;
import pf.utility.PFBrowser;
import pf.utility.PFDataReader;



public class PFTestOne {
	
	public static void main(String[] args) {

	WebDriver driver=null;
	PFDataReader.path = "D:\\Automation\\Selenium\\InitialData.txt";
	driver = PFBrowser.setBowser(driver, PFDataReader.getData("Browser"));
	driver.get(PFDataReader.getData("url"));
	
	// Actual Test //

	PFLogin login = new PFLogin(driver);		
	login.setUserName(PFDataReader.getData("LoginID")).setPassword(PFDataReader.getData("Password")).clickbtn_Login().
	clickBtn_AdminSection().clickBtn_Qualification().clickBtn_Education().clickCheckBox_highest().clickBtn_Add();
	
	System.out.println("done");
	
	
	}
}
