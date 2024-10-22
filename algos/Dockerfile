# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install required Python packages
#RUN pip install --no-cache-dir -r requirements.txt

RUN pip install pandas==2.0.3
RUN pip install kiteconnect==4.1.0
RUN pip install numpy==1.25.0
RUN pip install statsmodels==0.14.0
RUN pip install stocktrends==0.2.0

# Install cron to manage job scheduling
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Copy crontab configuration
COPY crontab.txt /etc/cron.d/trading-cron

# Give execution rights to the cron job script
RUN chmod 0644 /etc/cron.d/trading-cron

# Apply cron job configuration and start cron service
RUN crontab /etc/cron.d/trading-cron

# Start cron and the Python script
CMD cron -f
