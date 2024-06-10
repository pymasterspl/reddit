FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1

WORKDIR /code

RUN apt-get update && \
    apt-get install -y mc vim && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install poetry

RUN poetry config virtualenvs.in-project true

EXPOSE 8000
