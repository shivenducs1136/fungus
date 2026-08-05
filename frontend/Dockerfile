FROM node:20-alpine AS base

WORKDIR /app

# Copy package manifests first to leverage Docker cache
COPY package.json package-lock.json ./


FROM base AS build

# Optional build argument for Vite API base URL
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Install all dependencies required for build
RUN npm ci

# Copy application source
COPY . .

# Build production bundle
RUN npm run build


FROM nginx:alpine AS release

# Copy built static files to Nginx html directory
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]


FROM base AS dev

# Install all dependencies
RUN npm install

# Copy application source
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start development server binding to all network interfaces
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
