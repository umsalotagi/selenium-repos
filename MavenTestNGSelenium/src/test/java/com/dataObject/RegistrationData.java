package com.dataObject;

import org.testng.annotations.DataProvider;

public class RegistrationData {
	
	
	public String firstName;
	public String lastName;
	public String phone;
	public String userName;
	
	public String country;
	public String email;
	public String password;
	
	public String confirmPassword;
	
	
	
	public String getFirstName() {
		return firstName;
	}
	public void setFirstName(String firstName) {
		this.firstName = firstName;
	}
	public String getLastName() {
		return lastName;
	}
	public void setLastName(String lastName) {
		this.lastName = lastName;
	}
	public String getPhone() {
		return phone;
	}
	public void setPhone(String phone) {
		this.phone = phone;
	}
	public String getUserName() {
		return userName;
	}
	public void setUserName(String userName) {
		this.userName = userName;
	}
	public String getCountry() {
		return country;
	}
	public void setCountry(String country) {
		this.country = country;
	}
	public String getEmail() {
		return email;
	}
	public void setEmail(String email) {
		this.email = email;
	}
	public String getPassword() {
		return password;
	}
	public void setPassword(String password) {
		this.password = password;
	}
	
	public String getConfirmPassword() {
		return confirmPassword;
	}
	public void setConfirmPassword(String confirmPassword) {
		this.confirmPassword = confirmPassword;
	}
	
	
	// ###################### Data provider method
	
	@DataProvider (name = "regData")
	public static Object[][] getRegistrationData() {
		return new Object[][] { {"Deepika", "Padukon", "8089657898", "Deepika@me.in", "INDIA",
			"IDeepika", "Ummm", "Ummm"}, {"Jacklin", "Fernandice","7645679082", "Jacklin@me.in",
				"SINGAPORE", "IJacklin", "Jmmm", "Jmmm"} };
	}
	
	
	

}
