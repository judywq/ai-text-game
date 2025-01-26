FROM node:18-bullseye-slim

WORKDIR /app/vue_frontend

COPY ./vue_frontend/package.json /app/vue_frontend
COPY ./.envs/.local/.env.development ${APP_HOME}/vue_frontend/.env.development

COPY ./compose/local/vite/entrypoint /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint

RUN npm install && npm cache clean --force

ENV PATH ./node_modules/.bin/:$PATH

ENTRYPOINT ["/entrypoint"]
