# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set environment variables
ENV root_pw=${root_pw}
ENV port_mapping=${port_mapping}
ENV MYSQL_ROOT_PASSWORD=${mysql_root_pw}

# Set the working directory in the container to /app
WORKDIR /app

# Add the app directory contents into the container at /app
ADD app /app

# Upgrade pip and setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools


# Install necessary packages, including cron
RUN apt-get update && \
    apt-get -y install gcc mono-mcs cron && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Add your cron job file
ADD cronjob /etc/cron.d/keep-db-alive

# Give execution rights on the cron job and apply it
RUN chmod 0644 /etc/cron.d/keep-db-alive && \
    crontab /etc/cron.d/keep-db-alive

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Command to start the services
CMD cron && tail -f /var/log/cron.log & streamlit run db_hack.py