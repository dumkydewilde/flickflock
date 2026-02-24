FROM python:3.13-slim

ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
ENV PORT 8080

WORKDIR $APP_HOME
COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

# Persistent data directory for SQLite and cache
RUN mkdir -p /app/data
VOLUME ["/app/data"]

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
