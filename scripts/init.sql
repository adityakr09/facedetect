-- Initialisation script – runs once when the postgres container is first created.
-- Alembic handles subsequent schema migrations.

-- Enable uuid generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE DATABASE facedetect;
