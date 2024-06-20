# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Install necessary packages
RUN apt-get update && \
    apt-get -y install gcc mono-mcs && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container to /app
WORKDIR /app

# Add the app directory contents into the container at /app
ADD app /app

# Upgrade pip and setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Run db_hack.py when the container launches
CMD ["sh", "-c", "sleep 5 && streamlit run db_hack.py"]