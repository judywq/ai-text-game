FROM node:18-bullseye-slim as vite-builder
ARG IS_STAGING="false"
ARG APP_HOME=/app

# Copy only package files first to leverage Docker cache
COPY ./vue_frontend/package*.json ${APP_HOME}/vue_frontend/
WORKDIR ${APP_HOME}/vue_frontend

# Use cache mount to speed up npm install
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Copy the rest of the application
COPY . ${APP_HOME}
COPY ./.envs/.staging/.env.staging ${APP_HOME}/vue_frontend/
COPY ./.envs/.production/.env.production ${APP_HOME}/vue_frontend/

RUN pwd
RUN ls -la .

# Conditional build based on IS_STAGING
RUN if [ "$IS_STAGING" = "true" ]; then \
  npm run build:staging; \
    else \
  npm run build; \
    fi


FROM docker.io/nginx:1.17.8-alpine
COPY ./compose/production/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=vite-builder /app/vue_frontend/dist /usr/share/nginx/html/vue
