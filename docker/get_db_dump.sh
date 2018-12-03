#!/bin/sh

cd "$(dirname "$0")"
docker-compose exec db pg_dumpall -c -U postgres | gzip
