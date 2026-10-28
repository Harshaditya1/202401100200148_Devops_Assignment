import logging
import os
import socket
import time

import psycopg2
from flask import Flask, jsonify, request
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = app.logger


def database_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "festpass"),
        user=os.getenv("DB_USER", "festpass"),
        password=os.getenv("DB_PASSWORD", ""),
        connect_timeout=3,
    )


def initialize_database():
    for attempt in range(5):
        try:
            with database_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS registrations (
                            id SERIAL PRIMARY KEY,
                            name TEXT NOT NULL,
                            email TEXT NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
            logger.info("Database schema is ready")
            return
        except psycopg2.Error:
            if attempt == 4:
                logger.warning("Database is unavailable; API will report its status")
                logger.exception("Could not initialize database schema")
            else:
                time.sleep(1)


@app.get("/api/health")
def health():
    database_status = False
    try:
        with database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        database_status = True
    except psycopg2.Error:
        logger.exception("Database health check failed")

    return jsonify(
        {
            "registration_number": os.getenv("REGNO", "REGNO_NOT_SET"),
            "version": os.getenv("APP_VERSION", "0.1.0"),
            "container_hostname": socket.gethostname(),
            "database_status": database_status,
        }
    )


@app.get("/api/registrations")
def list_registrations():
    try:
        with database_connection() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, name, email, created_at FROM registrations ORDER BY id"
                )
                registrations = cursor.fetchall()
        for registration in registrations:
            registration["created_at"] = registration["created_at"].isoformat()
        return jsonify(registrations)
    except psycopg2.Error:
        logger.exception("Could not list registrations")
        return jsonify({"error": "Database is unavailable"}), 503


@app.post("/api/registrations")
def create_registration():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "A JSON request body is required"}), 400

    name = payload.get("name")
    email = payload.get("email")
    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "name must be a non-empty string"}), 400
    if not isinstance(email, str) or not email.strip():
        return jsonify({"error": "email must be a non-empty string"}), 400

    try:
        with database_connection() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO registrations (name, email)
                    VALUES (%s, %s)
                    RETURNING id, name, email, created_at
                    """,
                    (name.strip(), email.strip()),
                )
                registration = cursor.fetchone()
        registration["created_at"] = registration["created_at"].isoformat()
        return jsonify(registration), 201
    except psycopg2.Error:
        logger.exception("Could not create registration")
        return jsonify({"error": "Database is unavailable"}), 503


initialize_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
