# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for Python packages (e.g., Pillow requires libs)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the entire project code into the container
COPY . /app/

# Expose the port where the ASGI server (Daphne) will listen
EXPOSE 8000

# The command to run the ASGI server (Daphne)
# We bind to 0.0.0.0 so that the server is accessible outside the container's localhost.
# The project name is 'auction_project'.
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "auction_project.asgi:application"]
