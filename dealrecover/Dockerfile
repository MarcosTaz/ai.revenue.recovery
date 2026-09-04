FROM node:22-alpine
WORKDIR /app
COPY managed-src-v0.7.2.tgz.b64 /tmp/managed-src.tgz.b64
RUN base64 -d /tmp/managed-src.tgz.b64 > /tmp/managed-src.tgz \
 && echo "1016ebb297cd0efe14bc80f1e0e2b0e759fe55e7c393428b5ada92b1bb646673  /tmp/managed-src.tgz" | sha256sum -c - \
 && tar -xzf /tmp/managed-src.tgz -C /app \
 && rm -f /tmp/managed-src.tgz /tmp/managed-src.tgz.b64
COPY package.json ./
COPY src/managedBootstrap.js ./src/managedBootstrap.js
COPY src/managedHttpApi.js ./src/managedHttpApi.js
COPY src/opaqueSessionAuth.js ./src/opaqueSessionAuth.js
COPY src/postgresBlobStore.js ./src/postgresBlobStore.js
RUN npm install --omit=dev --ignore-scripts --no-audit --no-fund \
 && npm cache clean --force
ENV NODE_ENV=production HOST=0.0.0.0 DEALRECOVER_DEPLOY_MODE=health-only
EXPOSE 3000
USER node
CMD ["node","managed-server.mjs"]
