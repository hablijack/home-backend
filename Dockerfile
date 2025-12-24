FROM python:3.13-alpine

RUN apk add --update --no-cache python3-dev gcc libc-dev libffi-dev && \
    apk upgrade

ADD app /app

RUN mkdir /app/log

RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

CMD [ "python", "/app/main.py" ]

EXPOSE 8080/tcp
