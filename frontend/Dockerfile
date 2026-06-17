FROM node:20-slim

WORKDIR /app

COPY package.json /app/
RUN npm install

COPY . /app/

# Build production assets
RUN npm run build

# Copy build to shared volume on startup and hold container alive
CMD ["sh", "-c", "mkdir -p /var/www/frontend && cp -r dist/* /var/www/frontend/ && echo 'Frontend files copied successfully to volume.' && tail -f /dev/null"]
