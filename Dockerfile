# Use the official Python 3.11 image as the base image
FROM python:3.11

# Set the working directory within the container
WORKDIR /flask-app-tt

# Copy the necessary files and directories into the container
COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Define the command to run the Flask application using Gunicorn
CMD ["gunicorn", "--timeout", "1200", "--workers", "1" , "--threads", "4", "-b", "0.0.0.0:8080", "app:app"]