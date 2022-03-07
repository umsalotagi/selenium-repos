package sizeOfTaskBar;

import java.awt.Dimension;
import java.awt.GraphicsDevice;
import java.awt.GraphicsEnvironment;
import java.awt.Insets;
import java.awt.Rectangle;
import java.awt.Toolkit;
import java.awt.geom.Area;

public class TaskBarSizer {
	
	public static void main(String[] args) {
		
	
	Dimension scrnSize = Toolkit.getDefaultToolkit().getScreenSize();

	Rectangle winSize = GraphicsEnvironment.getLocalGraphicsEnvironment().getMaximumWindowBounds();

	int taskBarHeight = scrnSize.height - winSize.height;
	int taskBarWidth = scrnSize.width - winSize.width;
	System.out.println("height " + taskBarHeight + "      width: " + taskBarWidth);
	System.out.println("screenSize: " + scrnSize.height + " width: " + scrnSize.width );
	System.out.println(winSize.height + "   " +  winSize.width);
	
	GraphicsDevice gd = GraphicsEnvironment.getLocalGraphicsEnvironment().getDefaultScreenDevice();
	Rectangle bounds = gd.getDefaultConfiguration().getBounds();
	Insets insets = Toolkit.getDefaultToolkit().getScreenInsets(gd.getDefaultConfiguration());
	
	Rectangle safeBounds = new Rectangle(bounds);
	safeBounds.x += insets.left;
	safeBounds.y += insets.top;
	safeBounds.width -= (insets.left + insets.right);
	safeBounds.height -= (insets.top + insets.bottom);

	System.out.println("Bounds = " + bounds);
	System.out.println("SafeBounds = " + safeBounds);

	Area area = new Area(bounds);
	area.subtract(new Area(safeBounds));
	System.out.println("Area = " + area.getBounds());
	
	System.out.println("all dimensions " + area.getBounds().x + " " + area.getBounds().y + " " + area.getBounds().width
			+ " " + area.getBounds().height);
	
	System.out.println(safeBounds.getCenterX() + "   " + safeBounds.getCenterY());

	
	 GraphicsDevice gdA = GraphicsEnvironment.getLocalGraphicsEnvironment().getDefaultScreenDevice();
	 int widthA = gdA.getDisplayMode().getWidth();
	 int heightA = gdA.getDisplayMode().getHeight();
	 
	 
	 
	
	
	
	}

}
