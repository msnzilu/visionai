FROM nginx:alpine

# Copy static assets directly to Nginx web root
COPY . /usr/share/nginx/html

# Overwrite default config with our custom one
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]