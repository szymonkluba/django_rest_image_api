# syntax=docker/dockerfile:1
FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY image_api /code/
RUN chmod 775 ./scripts/wait-for-it.sh
RUN chmod 775 ./scripts/django_setup.sh
