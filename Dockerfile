# Use the official PyPy3 slim image for faster performance.
FROM pypy:3-slim

# Install ImageMagick.
RUN apt-get update && apt-get install -y imagemagick && rm -rf /var/lib/apt/lists/*

# Set the working directory.
WORKDIR /app

# Copy the application code.
COPY app.py /app/app.py

# Install aiohttp.
RUN pip install aiohttp

# Expose the port (default 5000).
EXPOSE 5000

# Run the application using pypy3.
CMD ["pypy3", "app.py"]
