#!/bin/bash
# pg_dump of db screeps -> var/backups (keep 8) + copy of newest into the agent store (second persistent copy).
#   tools/pg_backup.sh            dump if newest is older than 6h (called by services.sh every patrol)
#   tools/pg_backup.sh --force    dump now
#   tools/pg_backup.sh --restore  restore newest dump into an EMPTY cluster (used by services.sh only)
cd "$(dirname "$0")/.."; set -a; . ./.env; set +a
BK=var/backups; STORE=/cursor/stores/store-f5e64756-d470-477c-ba13-d4d68ba2bcd9/screeps-db
mkdir -p $BK; export PGHOST=127.0.0.1 PGUSER=screeps
if [ "$1" = --restore ]; then
  f=$(ls -t $BK/screeps-*.dump $STORE/screeps-*.dump 2>/dev/null | head -1)
  sudo -u postgres psql -qc "DO \$\$BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='screeps') THEN CREATE ROLE screeps LOGIN PASSWORD '$PGPASSWORD'; END IF; END\$\$" \
    && sudo -u postgres createdb -O screeps screeps && sudo -u postgres psql -qd screeps -c 'CREATE EXTENSION timescaledb' || exit 1
  if [ -z "$f" ]; then echo "no backup found: empty DB + schema"; .venv/bin/python tools/db.py --init; exit; fi
  echo "restore $f"; sudo -u postgres psql -qd screeps -c 'SELECT timescaledb_pre_restore()' >/dev/null
  sudo -u postgres pg_restore -d screeps "$f" 2>&1 | grep -v -i 'already exists' | tail -5
  sudo -u postgres psql -qd screeps -c 'SELECT timescaledb_post_restore()' >/dev/null; exit 0
fi
newest=$(ls -t $BK/screeps-*.dump 2>/dev/null | head -1)
[ "$1" != --force ] && [ -n "$newest" ] && [ -z "$(find "$newest" -mmin +360)" ] && exit 0
f=$BK/screeps-$(date +%Y%m%d-%H%M).dump
pg_dump -Fc -Z9 -f "$f.tmp" screeps 2>/dev/null && mv "$f.tmp" "$f" || { rm -f "$f.tmp"; echo "pg_dump failed"; exit 1; }
ls -t $BK/screeps-*.dump | tail -n +9 | xargs -r rm -f
mkdir -p $STORE && cp "$f" $STORE/ && ls -t $STORE/screeps-*.dump | tail -n +3 | xargs -r rm -f
echo "backup $f $(du -h "$f" | cut -f1)"
