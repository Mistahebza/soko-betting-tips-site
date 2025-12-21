FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . /app

EXPOSE 5000

# Run with gunicorn for production
CMD ["gunicorn", "app:application", "-w", "2", "-b", "0.0.0.0:5000"]
