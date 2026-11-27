#!/bin/sh

[ -d .venv ] && . .venv/bin/activate

alembic upgrade head
alembic revision --autogenerate -m "$*"
