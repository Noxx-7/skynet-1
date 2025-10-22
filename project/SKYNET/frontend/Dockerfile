FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port 5000 (as configured in package.json)
EXPOSE 5000

# Start the development server (or use production build)
# For production, uncomment the build command below:
# RUN npm run build
# CMD ["npm", "start"]

# For development:
CMD ["npm", "run", "dev"]
