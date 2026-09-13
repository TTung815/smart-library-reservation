FROM nginx:1.25-alpine

# Cài đặt curl phục vụ healthcheck
RUN apk add --no-cache curl

# Xóa cấu hình mặc định của Nginx
RUN rm -f /etc/nginx/conf.d/default.conf


# Copy cấu hình Nginx Reverse Proxy
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

