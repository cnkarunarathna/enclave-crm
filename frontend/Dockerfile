# syntax=docker/dockerfile:1
# Builds the React app, then serves the static files with nginx.

# ---- build: install exact locked dependencies and produce dist/
FROM node:24-alpine AS build
WORKDIR /app
# Git hooks are for developer machines; skip husky's install in the image.
ENV HUSKY=0
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Baked in at build time (Vite inlines it). The default is same-origin: nginx
# below proxies /api/ to the backend, so the browser needs no CORS.
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

# ---- runtime: static files only, no Node
FROM nginx:1.29-alpine
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
