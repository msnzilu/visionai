FROM node:18-bullseye-slim

WORKDIR /app

# Install system dependencies required by Playwright
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    libgbm1 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright system dependencies as root
RUN npx --yes playwright@latest install-deps chromium

# Create non-root user and give ownership of /app
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Copy package files
COPY --chown=appuser:appuser package*.json ./

# Install dependencies
RUN npm install

# Install Playwright browsers (without --with-deps since we already installed deps)
RUN npx playwright install chromium

# Copy application code
COPY --chown=appuser:appuser . .

EXPOSE 3000

CMD ["node", "src/index.js"]