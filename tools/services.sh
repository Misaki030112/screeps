#!/bin/bash
# Start-if-down for all box services (no systemd): PostgreSQL+TimescaleDB, Grafana, websocket listener, dashboard.
# Idempotent; the patrol runs it each iteration.  Usage: tools/services.sh
# Persistence (see docs/DATA.md "Box restarts"): a box update resets system dirs (/usr, /etc, /var/lib, apt packages)
# but keeps /workspace.  So PGDATA lives in var/pg17 and Grafana data in grafana/data (both under /workspace, gitignored);
# this script only reinstalls packages and re-registers the existing cluster.  It NEVER initdb's over existing data.
cd "$(dirname "$0")/.."
ROOT=$PWD; set -a; . ./.env; set +a
PGDIR=$ROOT/var/pg17; BK=$ROOT/var/backups
ok() { echo "ok   $1"; }; start() { echo "start $1"; }; die() { echo "ERROR $1" >&2; exit 3; }

# 1. packages (reinstalled only when missing)
if ! dpkg -s postgresql-17 postgresql-17-timescaledb >/dev/null 2>&1; then start apt-postgres
  sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq postgresql-17 postgresql-17-timescaledb >/dev/null || die "apt install postgres"; fi
if [ ! -x /usr/share/grafana/bin/grafana ]; then start apt-grafana
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$ROOT"/var/pkgs/grafana_*_amd64.deb >/dev/null || die "grafana deb (var/pkgs)"; fi
if [ ! -x .venv/bin/python ]; then start venv; python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt || die venv; fi

# 2. cluster 17/main must point at $PGDIR
cur=$(pg_lsclusters -h 2>/dev/null | awk '$1==17 && $2=="main"{print $6}')
if [ "$cur" != "$PGDIR" ]; then
  if [ -n "$cur" ]; then   # e.g. the default cluster apt creates on a fresh install
    sudo pg_ctlcluster 17 main start 2>/dev/null
    if sudo -u postgres psql -Atqc "select 1 from pg_database where datname='screeps'" 2>/dev/null | grep -q 1; then
      die "cluster 17/main at $cur holds a screeps DB but is not $PGDIR; refusing to touch it (move it by hand)"; fi
    start "drop-empty-default-cluster $cur"; sudo pg_dropcluster --stop 17 main || die dropcluster
  fi
  if sudo test -f "$PGDIR/PG_VERSION"; then start "adopt $PGDIR"
    # pg_createcluster adopts a data dir only if the conf files sit inside it; it then moves them to /etc
    for f in postgresql.conf pg_hba.conf pg_ident.conf; do sudo install -o postgres -m 644 "$ROOT/var/pg17-conf/$f" "$PGDIR/$f"; done
    sudo pg_createcluster 17 main -d "$PGDIR" >/dev/null || die "adopt cluster"
  else
    # no data dir: create one and restore the newest backup (never an empty DB silently)
    sudo test -e "$PGDIR" && sudo find "$PGDIR" -mindepth 1 -print -quit | grep -q . && die "$PGDIR not empty but no PG_VERSION"
    start "new cluster $PGDIR"; sudo pg_createcluster 17 main -d "$PGDIR" >/dev/null || die createcluster
    NEED_RESTORE=1
  fi
  sudo mkdir -p /etc/postgresql/17/main/conf.d && sudo cp db/postgres-screeps.conf /etc/postgresql/17/main/conf.d/screeps.conf
  for f in postgresql.conf pg_hba.conf pg_ident.conf; do sudo cat /etc/postgresql/17/main/$f > var/pg17-conf/$f; done   # keep for next adopt
fi
if pg_lsclusters -h | awk '$1==17 && $2=="main"{print $4}' | grep -q online; then ok postgres; else start postgres; sudo pg_ctlcluster 17 main start || die "pg start"; fi
# Apache Timescale: plain views stand in for continuous aggregates (Grafana); idempotent
if [ -f db/views_apache.sql ]; then
  PGPASSWORD=$PGPASSWORD psql -h 127.0.0.1 -U screeps -d screeps -v ON_ERROR_STOP=1 -f db/views_apache.sql >/dev/null && ok views_apache || echo "WARN views_apache failed"
fi
if [ -n "$NEED_RESTORE" ]; then tools/pg_backup.sh --restore || die restore; fi

# 3. other services
if pgrep -f "[g]rafana server" >/dev/null; then ok grafana; else start grafana
  GF_SECURITY_ADMIN_PASSWORD=$GF_ADMIN_PASSWORD PGPASSWORD=$PGPASSWORD nohup /usr/share/grafana/bin/grafana server --homepath /usr/share/grafana --config grafana/grafana.ini >> metrics/grafana.out 2>&1 & fi
if pgrep -f "[r]un_listener.sh" >/dev/null; then ok listener; else start listener; nohup tools/run_listener.sh >/dev/null 2>&1 & fi
if pgrep -f "[h]ttp.server 8787" >/dev/null; then ok dashboard; else start dashboard; nohup tools/run_dashboard.sh >> metrics/dashboard.out 2>&1 & fi

# 4. backup (no-op unless the newest dump is older than 6h)
tools/pg_backup.sh || echo "WARN backup failed"
