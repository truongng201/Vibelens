FROM nginx:1.27.4-alpine-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends certbot python3-certbot-nginx && \
    rm -rf /var/lib/apt/lists/*

CMD ["nginx", "-g", "daemon off;"]