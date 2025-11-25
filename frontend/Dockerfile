FROM node:22-alpine

WORKDIR /app

# Install dependencies first (leveraging Docker layer cache)
# Use npm ci when possible for reproducible installs
COPY package.json package-lock.json* ./
RUN npm ci --silent || npm install --legacy-peer-deps --silent

# Copy the rest of the app
COPY . .

# For dev: enable chokidar polling so file changes on the host are detected
# This is especially useful on Windows / Docker Desktop mounts.
ENV CHOKIDAR_USEPOLLING=true
ENV CHOKIDAR_INTERVAL=100
ENV NODE_ENV=development

EXPOSE 3000

# Run Vite dev server listening on all interfaces so HMR works from the host.
# When using this image for development, mount your source directory as a volume
# (so edits on the host are visible inside the container). Example docker run:
# docker run -p 3000:3000 -v "$(pwd)":/app -v /app/node_modules <image>
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
