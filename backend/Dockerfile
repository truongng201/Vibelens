## base image
FROM python:3.13-alpine AS compile-image

## install dependencies
RUN apk update && \
    apk add --no-cache \
    libpq-dev \
    gcc \
    python3-dev \
    build-base \
    g++ \
    musl-dev \
    linux-headers

## virtualenv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

## add and install requirements
RUN pip install --upgrade pip && pip install pip-tools
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

## build-image
FROM python:3.13-alpine AS runtime-image

## install nc
RUN apk update && \
    apk add --no-cache curl libpq

## copy Python dependencies from build image
COPY --from=compile-image /opt/venv /opt/venv

## set working directory
WORKDIR /home/dev

RUN echo -e 'CipherString = DEFAULT@SECLEVEL=1' >>/etc/ssl/openssl.cnf

## add user
RUN addgroup -S dev && adduser -S dev -G dev
RUN mkdir -p /home/dev && \
    chown -R dev:dev /home/dev

# copy source code
COPY . /home/dev

# switch to non-root user
USER dev

## set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/opt/venv/bin:$PATH"

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]