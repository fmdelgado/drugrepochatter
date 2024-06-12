# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set environment variables
ENV root_pw=${root_pw}
ENV port_mapping=${port_mapping}
ENV MYSQL_ROOT_PASSWORD=${mysql_root_pw}

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Upgrade pip and setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools

# Install necessary packages
RUN apt-get update && \
    apt-get -y install gcc mono-mcs && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Run db_hack.py when the container launches
CMD ["streamlit", "run", "db_hack.py"]
