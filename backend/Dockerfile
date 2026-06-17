FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies using development requirements
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r /app/requirements/development.txt

# Copy entrypoint and application code
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

COPY . /app/

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
