#!/bin/bash

set -e

if [ ! -f .env ]; then
    cp env-template .env
    echo "${0}: cp env-template .env "
else
    echo "${0}: The .env file already exists."
fi

echo "${0}: poetry install"
poetry install


echo "${0}: running migrations"
poetry run python manage.py migrate --noinput


echo "${0}: start server"
poetry run python manage.py runserver 0.0.0.0:8000
