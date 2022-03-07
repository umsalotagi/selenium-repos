package pf.functions;

public class MakeSleep {
	
	public MakeSleep sleep(long  time) {
		
		try {
			Thread.sleep(time);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			System.out.println("Error in thread.sleep in Makesleep class");
			e.printStackTrace();
		}
		
		return this;
		
	}

}
