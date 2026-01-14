# Use official Python runtime as base image
FROM python:3.10-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the streamlit app
COPY streamlit_app.py .

# Create .streamlit directory and config
RUN mkdir -p ~/.streamlit/

# Configure streamlit to run without a browser
RUN echo "\
[logger]\n\
level = \"info\"\n\
\n\
[client]\n\
showErrorDetails = true\n\
" > ~/.streamlit/config.toml

# Expose the default Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
