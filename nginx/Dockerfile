FROM nginx:alpine

# Install dependencies and create nginx user/group
RUN apk add --no-cache curl \
    && addgroup -S nginx \
    && adduser -S -G nginx nginx

# Set working directory
WORKDIR /usr/share/nginx/html

# Copy custom Nginx configuration
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY ./default.conf /etc/nginx/conf.d/default.conf

# Copy static files
COPY ./public .

# Set