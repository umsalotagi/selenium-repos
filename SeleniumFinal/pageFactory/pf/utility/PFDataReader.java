package pf.utility;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

public class PFDataReader {
	
	
	static BufferedReader reader;
	static FileReader data;
	public String browser;
	public String login;
	String[] temp2;
	public String password;
	public static String path ;
		
	public static String getData( String Tag) {
		
		String returnData=null;

		try {
			data = new FileReader (path);
			reader = new BufferedReader(data);
				
			String temp;
			while ( ( temp = reader.readLine())  != null ) {
				String [] tagSet = temp.split(";");
				if (tagSet[0].equals(Tag) && tagSet.length > 1) {
					returnData = tagSet[1];
				}
				
			}
			
			if ( returnData  == null) {		
				throw new NullPointerException();
			}
							
		} catch (IOException e) {
			e.printStackTrace();
		}
		catch (NullPointerException e) {
			System.out.println("\nData Not Available \nExit.");
			System.exit(0);
		}
		
		return returnData;
	}

}
