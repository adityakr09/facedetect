FROM node:20-alpine AS builder

ARG VITE_API_BASE=""
ENV VITE_API_BASE=$VITE_API_BASE

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# ── Production stage (serve via nginx inside this container) ──────────────────
FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
