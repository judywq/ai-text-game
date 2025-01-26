# AI Text Game

The web UI for Automated Writing Evaluation system.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## Settings

Moved to [settings](https://cookiecutter-django.readthedocs.io/en/latest/1-getting-started/settings.html).

## Basic Commands

### Running the Vite Dev Server

This app integrates with a Vue frontend located in `vue_frontend`.

##### With Docker
The Vite dev server will automatically run in docker when started with the docker-compose.local.yml configuration.
```sh
cp ./envs/.local/.secrets.example ./envs/.local/.secrets
docker-compose -f docker-compose.local.yml up
```

##### From the console
Alternatively you, may run the Vite dev server directly from the project directory:
```sh
cd vue_frontend
npm install
npm run dev
````

For more information, refer to the [Vue3 Vite Django Cookiecutter project](https://github.com/ilikerobots/cookiecutter-vue-django).



### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy ai_text_game

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally.html#using-webpack-or-gulp).

### Celery

This app comes with Celery.

To run a celery worker:

```bash
cd ai_text_game
celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important _where_ the celery commands are run. If you are in the same folder with _manage.py_, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

```bash
cd ai_text_game
celery -A config.celery_app beat
```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

```bash
cd ai_text_game
celery -A config.celery_app worker -B -l info
```

### Email Server

In development, it is often nice to be able to see emails that are being sent from your application. For that reason local SMTP server [Mailpit](https://github.com/axllent/mailpit) with a web interface is available as docker container.

Container mailpit will start automatically when you will run all docker containers.
Please check [cookiecutter-django Docker documentation](https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally-docker.html) for more details how to start all containers.

With Mailpit running, to view messages that are sent by your application, open your browser and go to `http://127.0.0.1:8025`

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=cookiecutter> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

## Deployment

The following details how to deploy this application.

### Heroku

See detailed [cookiecutter-django Heroku documentation](https://cookiecutter-django.readthedocs.io/en/latest/3-deployment/deployment-on-heroku.html).

### Vue

For production deployment, the Vue frontend must be built into static resources, which will be served
using the same Django staticfiles strategy as the rest of your site.

If you are using the production Docker configuration, this will be performed automatically when the images are built.

Otherwise, you must build the static assets yourself as part of your build and deploy process, sometime before the
`collectstatic` management command is run. The static assets may be built by running `npm run build` from within the
`vue_frontend` directory. The resulting files will be placed into the `ai_text_game/static/vue` directory
and are handled subsequently as standard static assets.

Note the setting `VUE_FRONTEND_USE_DEV_SERVER` dictates whether your Django app will be expecting to serve Vue assets
from the Vite Dev Server or from a static build.  This setting defaults to the same as `DEBUG`, but can be modified as
needed.
If you wish to build static Vue assets on the local Docker configuration, you may run:
`docker-compose -f local.yml run vite vite build`

For more information, refer to the [Vue3 Vite Django Cookiecutter project](https://github.com/ilikerobots/cookiecutter-vue-django).

### Docker

See detailed [cookiecutter-django Docker documentation](https://cookiecutter-django.readthedocs.io/en/latest/3-deployment/deployment-with-docker.html).
