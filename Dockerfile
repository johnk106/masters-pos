
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=admin.settings

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         libpq-dev \
         gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . /app

RUN python manage.py collectstatic --noinput

RUN python manage.py migrate

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
