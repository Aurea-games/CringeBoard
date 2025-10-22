FROM node:22-alpine

WORKDIR /app

# Install dependencies first (leveraging Docker layer cache)
COPY package.json package-lock.json* ./
RUN npm install --silent || npm install --legacy-peer-deps --silent

# Copy the rest of the app
COPY . .

EXPOSE 3000

CMD ["sh", "-c", "npm install && npm run dev -- --host 0.0.0.0 --port 3000"]
