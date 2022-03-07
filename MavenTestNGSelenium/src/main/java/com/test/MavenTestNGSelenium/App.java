package com.test.MavenTestNGSelenium;

/**
 * Hello world!
 *
 */
public class App 
{
    public static void main( String[] args )
    {
    	
    	//0 1 1 2 3 5 8 13 21
        System.out.println( "Hello World!" );
        
        int p=-1;
        int n=1;
        for (int i=0; i<=10;i++) {
        	
        	int o = p+n;
        	System.out.println(o);
        	p=n;
        	n=o;
        }
        
        
        int[] x = {10, 20, 30, 40, 50, 60};
        for (int i=0; i<x.length;i++) {
        	
        }
        
        
    }
}
