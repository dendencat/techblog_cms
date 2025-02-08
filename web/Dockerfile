FROM python:3.11-slim-buster

WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Set up user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
RUN chown -R appuser:appgroup /app

USER appuser

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "techblog.wsgi:application", "--bind", "0.0.0.0:8000"]
