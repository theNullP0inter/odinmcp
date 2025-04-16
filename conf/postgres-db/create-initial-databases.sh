#!/bin/bash

set -e
set -u

echo "setting up intial databases";

PGPASSWORD="${POSTGRES_PASSWORD}" psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    
    CREATE USER heimdall PASSWORD 'heimdall';
    CREATE DATABASE heimdall OWNER heimdall;
    GRANT ALL PRIVILEGES ON DATABASE heimdall TO heimdall;

    -- you can copy paste multiple of these commands if you need to add more databases
EOSQL

echo "setup complete for initial databases";