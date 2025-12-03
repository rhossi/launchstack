# Stage 1: Dependencies
FROM node:18-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
# Copy package files
COPY package.json pnpm-lock.yaml* ./
# Install pnpm
RUN npm install -g pnpm
# Install dependencies
RUN pnpm install --frozen-lockfile
# Stage 2: Builder
FROM node:18-alpine AS builder
WORKDIR /app
# Environment variables will be provided at runtime by Kubernetes
# Install pnpm
RUN npm install -g pnpm
# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Build the application
RUN pnpm run build
# Stage 3: Runner
FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
# Copy necessary files from builder
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]