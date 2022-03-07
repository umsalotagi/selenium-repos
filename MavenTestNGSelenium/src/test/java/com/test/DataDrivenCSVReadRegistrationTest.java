package com.test;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;

import org.testng.annotations.DataProvider;
import org.testng.annotations.Parameters;
import org.testng.annotations.Test;

import com.dataObject.RegistrationData;
import com.pageObject.AccountCreationPage;
import com.pageObject.NewRegistration;

public class DataDrivenCSVReadRegistrationTest extends BaseRepeat2{
	
	@Test(dataProvider="myData2", groups = {"one"})
	public void onlyName(RegistrationData d) {
		NewRegistration cr = new NewRegistration(driver);
		cr.registerNewUser(d);
	}
	
	
	@DataProvider(name="myData2")
	//@Parameters("filepath")
	public Object[] [] myData2() {
		try {
			//String filepath = "D:\\data.txt";
			String filepath = getClass().getClassLoader().getResource("data.txt").getFile();
			LogReport.info("This is file path " + filepath);
			FileReader fr = new FileReader(new File(filepath));
			BufferedReader br = new BufferedReader(fr);
			String sCurrentLine;
			ArrayList ar = new ArrayList();

			while ((sCurrentLine = br.readLine()) != null) {
				String [] dataSetOne;
				dataSetOne = sCurrentLine.split(",");
				RegistrationData d = new RegistrationData();
				d.setFirstName(dataSetOne[0]);
				d.setLastName(dataSetOne[1]);
				d.setPhone(dataSetOne[2]);
				d.setUserName(dataSetOne[3]);
				d.setCountry(dataSetOne[4]);
				d.setEmail(dataSetOne[5]);
				d.setPassword(dataSetOne[6]);
				d.setConfirmPassword(dataSetOne[7]);
				RegistrationData[] array1 = {d};
				ar.add(array1);
				LogReport.info("DATA 2 " + sCurrentLine);
			}
			
			Object [][] k = new Object[ar.size()] [];
			for (int i=0; i<ar.size(); i++) {
				k[i] = (Object[]) ar.get(i);
			}
			return  (Object[][]) k;
		} catch (Exception e) {
			e.printStackTrace();
			return null;
		}
		
		
	}

}
