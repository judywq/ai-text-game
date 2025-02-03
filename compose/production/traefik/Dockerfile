FROM docker.io/traefik:3.3.3

# Get the IS_STAGING environment variable in the docker compose file
ARG IS_STAGING="false"

RUN mkdir -p /etc/traefik/acme \
  && touch /etc/traefik/acme/acme.json \
  && chmod 600 /etc/traefik/acme/acme.json

# Copy the appropriate config based on IS_STAGING
COPY ./compose/production/traefik/traefik.production.yml /etc/traefik/
COPY ./compose/production/traefik/traefik.staging.yml /etc/traefik/
RUN if [ "$IS_STAGING" = "true" ] ; then \
      cp /etc/traefik/traefik.staging.yml /etc/traefik/traefik.yml ; \
      echo "cp /etc/traefik/traefik.staging.yml /etc/traefik/traefik.yml" > /etc/traefik/log.txt; \
    else \
      cp /etc/traefik/traefik.production.yml /etc/traefik/traefik.yml ; \
    fi && \
    echo "rm /etc/traefik/traefik.*.yml"
