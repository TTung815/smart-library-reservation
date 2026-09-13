FROM nginx:1.25-alpine

# Xóa cấu hình mặc định của Nginx
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy cấu hình Nginx Reverse Proxy
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

