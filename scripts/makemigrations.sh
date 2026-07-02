#! /bin/bash

DATABASE_URL=postgres://postgres:postgres@localhost5434/neves-be \
    ./.venv/bin/python manage.py makemigrations
