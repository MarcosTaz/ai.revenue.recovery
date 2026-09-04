FROM node:22-alpine
WORKDIR /app
COPY package.json ./
COPY e2e.mjs ./
ENV NODE_ENV=production
EXPOSE 3000
USER node
CMD ["node","e2e.mjs"]
