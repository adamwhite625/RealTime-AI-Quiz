#!/bin/bash
set -e

# This script creates a second database for Keycloak
# The main DB 'quizmaster' is created automatically by the Docker env var POSTGRES_DB

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE keycloak_db;
    GRANT ALL PRIVILEGES ON DATABASE keycloak_db TO "$POSTGRES_USER";
EOSQL