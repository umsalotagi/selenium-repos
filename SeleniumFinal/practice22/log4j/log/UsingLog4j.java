package log4j.log;


public class UsingLog4j {
	
	public static void main(String[] args) {
		LoggerA.prerequisite();
		LoggerA.info("Done1");
		LoggerA.error("nothing");
		LoggerA.warning("dish");
	}

}
