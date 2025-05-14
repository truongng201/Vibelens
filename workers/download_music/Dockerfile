## base image
FROM python:3.11-slim AS compile-image

## install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    gcc \
    librdkafka-dev

## virtualenv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

## add and install requirements
RUN pip install --upgrade pip && pip install pip-tools
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

## build-image
FROM python:3.11-slim AS runtime-image

## install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    librdkafka-dev \
    ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

## copy Python dependencies from build image
COPY --from=compile-image /opt/venv /opt/venv

## set working directory
WORKDIR /usr/src/app
ENV TRANSFORMERS_CACHE=/usr/src/app/.cache
RUN echo -e 'CipherString = DEFAULT@SECLEVEL=1' >>/etc/ssl/openssl.cnf
RUN chmod 777 /usr/src/app/cookies.txt
## add user
RUN addgroup --system user && adduser --system --ingroup user user
RUN mkdir -p /usr/src/app && chown -R user:user /usr/src/app
RUN mkdir -p /usr/src/app/.cache && chown -R user:user /usr/src/app/.cache

# switch to non-root user
USER user

COPY . /usr/src/app

## set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/opt/venv/bin:$PATH"


CMD ["python", "main.py"]