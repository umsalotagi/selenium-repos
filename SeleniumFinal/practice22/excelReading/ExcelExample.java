package excelReading;

import java.io.FileInputStream;
import java.io.FileOutputStream;

import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.xssf.usermodel.XSSFSheet;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

public class ExcelExample {
	
	public static void main(String[] args) throws Exception {
		
		FileInputStream excelFile = new FileInputStream ("D:\\Automation\\Selenium\\DataForExample.xlsx");
		XSSFWorkbook excelWbook = new XSSFWorkbook (excelFile);
		
		XSSFSheet eSheet = excelWbook.getSheet("Sheet1");
		
		Cell cell = eSheet.getRow(2).getCell(2); // index starts with 0
		
		String name = cell.getStringCellValue();
		
		System.out.println(name);
		
		
		
		
		
		
		
		FileInputStream excelFileW = new FileInputStream ("D:\\Automation\\Selenium\\WriterForExample.xlsx");
		XSSFWorkbook excelWbookW = new XSSFWorkbook (excelFileW);
		
		//XSSFSheet eSheetW = excelWbook.getSheet("Sheet1");
		
		Row row = eSheet.getRow(2);
		Cell cellW = row.getCell(2, Row.RETURN_BLANK_AS_NULL); // index starts with 0
		
		
			cellW = row.createCell(2);
			cellW.setCellValue("Happy");
	
		
		FileOutputStream fo = new FileOutputStream("D:\\Automation\\Selenium\\WriterForExample.xlsx");
		
		excelWbook.write(fo);
		System.out.println("Done");
		fo.flush();
		
		
		
		
		
		
		
		
	}

}
