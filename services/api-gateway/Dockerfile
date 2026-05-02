FROM node:20-alpine3.21

WORKDIR /app

COPY --chown=node:node package.json package-lock.json* ./
RUN npm install --omit=dev

COPY --chown=node:node src/ ./src/

USER node

EXPOSE 4000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD wget -qO- http://127.0.0.1:4000/api/v1/health || exit 1

CMD ["node", "src/index.js"]
