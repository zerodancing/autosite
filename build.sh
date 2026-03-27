#!/usr/bin/env bash
set -o errexit

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-autoservice.settings_production}"
export DJANGO_DEBUG=0

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py collectstatic --noinput --clear
python manage.py migrate --noinput
python manage.py ensure_bootstrap_superuser
python manage.py ensure_demo_catalog
python manage.py check --deploy
