# Use the official Python image from the Docker Hub
FROM python:3.9-buster

# Set the working directory in the container
WORKDIR /app

# Install the required system packages for FiftyOne
RUN apt-get update && apt-get install -y \
    libcurl4 \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* 

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

RUN mkdir -p data/validation/data

# Expose port 5000 to the outside world
EXPOSE 5000

# Command to run the Flask application
CMD ["python", "app.py"]
