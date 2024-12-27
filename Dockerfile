# Dockerfile - Container instructions
# Use the official Python slim image to keep the container lightweight
FROM python:3.9-slim

# Create a working directory for the app
WORKDIR /app

# Copy the requirements file first, then install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask app code
COPY app.py ./
# Copy the templates folder so we can render index.html
COPY templates/ ./templates/

# Copy or create the media directory (if you have a local media folder, you can also mount it at runtime)
# If you have a local "media" folder, uncomment the following line:
# COPY media/ ./media/
RUN mkdir -p media

# Expose port 5000 for Flask
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]