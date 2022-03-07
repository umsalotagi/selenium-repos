package com.test;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.events.WebDriverEventListener;

public class MyWebDriverListener implements WebDriverEventListener{

	public void beforeNavigateTo(String url, WebDriver driver) {
		// TODO Auto-generated method stub
		
	}

	public void afterNavigateTo(String url, WebDriver driver) {
		LogReport.info("WEBDRIVER :  Navigate To : " + url);
		
	}

	public void beforeNavigateBack(WebDriver driver) {
		// TODO Auto-generated method stub
		
	}

	public void afterNavigateBack(WebDriver driver) {
		LogReport.info("WEBDRIVER :  Navigate Back");
		
	}

	public void beforeNavigateForward(WebDriver driver) {
		// TODO Auto-generated method stub
		
	}

	public void afterNavigateForward(WebDriver driver) {
		LogReport.info("WEBDRIVER :  Navigate Forward");
		
	}

	public void beforeNavigateRefresh(WebDriver driver) {
		// TODO Auto-generated method stub
		
	}

	public void afterNavigateRefresh(WebDriver driver) {
		LogReport.info("WEBDRIVER :  Navigate Refresh");
		
	}

	public void beforeFindBy(By by, WebElement element, WebDriver driver) {
		// TODO Auto-generated method stub
		
	}

	public void afterFindBy(By by, WebElement element, WebDriver driver) {
		if (element!=null) {
			LogReport.info("WEBDRIVER :  after find by : " + by.toString());
		}else {
			//LogReport.info("WEBDRIVER :  after find by : NULL" );
		}		
	}

	public void beforeClickOn(WebElement element, WebDriver driver) {
		// TODO Auto-generated method stub
		
	}

	public void afterClickOn(WebElement element, WebDriver driver) {
//		if (element.isDisplayed()) {
//			LogReport.info("WEBDRIVER :  after click on : " + element.getText());
//		}
		
//		LogReport.info("stttt" + element.toString());
//		try {
//			LogReport.info("WEBDRIVER :  after click on : " + element.getText());
//		} catch (Exception e) {
//			// LogReport.info("WEBDRIVER :  after click on : exception" );
//		}
	}

	public void beforeChangeValueOf(WebElement element, WebDriver driver) {
		// TODO Auto-generated method stub
		
	}

	public void afterChangeValueOf(WebElement element, WebDriver driver) {
		LogReport.info("WEBDRIVER :  after change value of : " + element.getAttribute("value"));
		
	}

	public void beforeScript(String script, WebDriver driver) {
		// TODO Auto-generated method stub
		
	}

	public void afterScript(String script, WebDriver driver) {
		LogReport.info("WEBDRIVER :  after Script " + script);
		
	}

	public void onException(Throwable throwable, WebDriver driver) {
		LogReport.info("WEBDRIVER :  onException " + throwable.getMessage());
		
	}

}
