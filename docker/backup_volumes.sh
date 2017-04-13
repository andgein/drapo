#!/bin/sh

BACKUP_DIR=/home/ructf/backup
WHEN=`date +%F_%H-%M-%S`

cd "$(dirname "$0")"
tar -cvpzf $BACKUP_DIR/volumes_$WHEN.tar.gz volumes
