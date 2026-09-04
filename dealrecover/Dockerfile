FROM node:22-alpine
WORKDIR /app
COPY package.json ./
COPY preview-server.mjs ./
ENV NODE_ENV=production HOST=0.0.0.0
EXPOSE 3000
USER node
CMD ["node","preview-server.mjs"]
