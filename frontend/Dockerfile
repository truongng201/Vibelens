# Step 1: Build the app
FROM node:23-slim AS build-image

# Set working directory
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy app source
COPY . .

# Build Next.js app
RUN npm run build

# Step 2: Serve the app
FROM node:23-slim AS run-image

# Set NODE_ENV to production
ENV NODE_ENV=production
ENV PORT=3000

# Create app directory
WORKDIR /app

# Copy only the necessary files from the builder
COPY --from=build-image /app/package.json ./
COPY --from=build-image /app/.next .next
COPY --from=build-image /app/public public
COPY --from=build-image /app/node_modules node_modules

# Expose port
EXPOSE 3000

# Start Next.js
CMD ["npm", "start"]
