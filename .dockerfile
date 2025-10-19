# Use official Playwright image with all dependencies
FROM mcr.microsoft.com/playwright/python:v1.38.0-focal

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE 5000

# Start Flask
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
