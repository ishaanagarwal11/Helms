# Use a lightweight Node base image
FROM node:16-alpine

# Create app directory
WORKDIR /usr/src/app

# Copy package.json/package-lock.json if you have them
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of your backend code
COPY . .

# Expose the application port (example 8080)
EXPOSE 8080

# Start the app
CMD ["node", "index.js"]
