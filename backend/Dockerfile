FROM python:3.13.18-slim-trixie

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app --no-create-home app

COPY --chown=10001:10001 app.py .

ARG APP_VERSION=0.2.0
ENV APP_VERSION=${APP_VERSION}

USER 10001:10001
EXPOSE 5000

CMD ["gunicorn", "--workers=2", "--bind=0.0.0.0:5000", "--access-logfile=-", "--error-logfile=-", "--preload", "app:app"]
