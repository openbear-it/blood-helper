FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json .
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# Replace the main nginx.conf so that conf.d/ is NOT included
COPY nginx.conf /etc/nginx/nginx.conf
# Remove the base-image default.conf (references a "backend" upstream that
# doesn't exist — routing is handled by Traefik at the cluster edge)
RUN rm -f /etc/nginx/conf.d/default.conf
# Pre-create writable temp dirs for non-root execution
RUN mkdir -p /tmp/client_body /tmp/proxy /tmp/fastcgi /tmp/uwsgi /tmp/scgi \
    && chown -R nginx:nginx /tmp/client_body /tmp/proxy /tmp/fastcgi /tmp/uwsgi /tmp/scgi
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
