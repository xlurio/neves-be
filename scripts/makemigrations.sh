#! /bin/bash

DATABASE_URL=postgres://postgres:postgres@localhost:5434/neves-be \
    ./.venv/bin/python manage.py makemigrations
