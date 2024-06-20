# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Install necessary packages
RUN apt-get update && \
    apt-get -y install gcc mono-mcs cron && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container to /app
WORKDIR /app

# Add the app directory contents into the container at /app
ADD app /app

# Upgrade pip and setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Add your cron job file
ADD cronjob /etc/cron.d/keep-db-alive

# Give execution rights on the cron job and apply it
RUN chmod 0644 /etc/cron.d/keep-db-alive && \
    crontab /etc/cron.d/keep-db-alive

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run db_hack.py when the container launches
CMD ["sh", "-c", "cron && tail -f /var/log/cron.log & sleep 5 && streamlit run db_hack.py"]