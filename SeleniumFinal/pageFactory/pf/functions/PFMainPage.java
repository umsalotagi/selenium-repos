package pf.functions;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.PageFactory;

public class PFMainPage extends MakeSleep{

	private WebDriver driver;

	public PFMainPage(WebDriver driver) {
		this.driver = driver;
		PageFactory.initElements(driver, this);
	}
	
	@FindBy (className ="firstLevelMenu")
	WebElement btn_AdminSection;
	
	@FindBy (id = "menu_admin_Qualifications")
	WebElement btn_Qualification;
	
	@FindBy (id = "menu_admin_viewEducation")
	WebElement btn_Education;
	
	@FindBy (css = "input[value='2']")
	WebElement checkBox_highest;
	
	@FindBy (id = "btnAdd")
	WebElement btn_Add;
	
	public PFMainPage clickBtn_AdminSection() {
		btn_AdminSection.click();
		return this;
	}
	
	public PFMainPage clickBtn_Qualification() {
		btn_Qualification.click();
		return this;
	}
	
	public PFMainPage clickBtn_Education() {
		btn_Education.click();
		return this;
	}
	
	public PFMainPage clickCheckBox_highest() {
		checkBox_highest.click();
		return this;
	}
	
	public PFMainPage clickBtn_Add() {
		btn_Add.click();
		return this;
	}
	
	
	

}
