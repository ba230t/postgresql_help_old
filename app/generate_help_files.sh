#!/bin/bash

# generate help files for postgres versions
# usage: ./generate_help_files.sh

VERSIONS=("9.6" "10" "11" "12" "13" "14")
PG_USER="postgres"

echo "Starting containers..."
for VERSION in "${VERSIONS[@]}"; do
  docker run --name postgres_$VERSION -e POSTGRES_PASSWORD=mysecretpassword -d postgres:$VERSION
done

echo "Generating help files..."
for VERSION in "${VERSIONS[@]}"; do
    CONTAINER_NAME=postgres_$VERSION
    KEYWORDS=$(docker exec -i $CONTAINER_NAME psql -U $PG_USER -c "\h" | sed -r "s/  +/\r\n/g" | sort | uniq | grep -v "^\s*$" | grep -v "Available help:")

    # output dirs for each version
    mkdir -p help_files/$CONTAINER_NAME

    # generates help texts
    IFS=$'\n' # keywords may has spaces like "CREATE DATABASE".
    for kw in $KEYWORDS; do
        echo "Processing command: $kw in $CONTAINER_NAME"
        docker exec -i $CONTAINER_NAME psql -U $PG_USER -c "\h $kw" > "help_files/$CONTAINER_NAME/${kw}.txt"
    done
done

echo "Removing containers..."
for VERSION in "${VERSIONS[@]}"; do
  docker rm -f postgres_$VERSION
done

echo "Finished generating help files."
