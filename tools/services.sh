#!/bin/bash
# Start-if-down for all box services (no systemd in this box): PostgreSQL+TimescaleDB, Grafana, websocket listener, dashboard.
# Idempotent; the patrol runs it each iteration, so everything comes back after a box restart.  Usage: tools/services.sh [status]
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
ok() { echo "ok   $1"; }; start() { echo "start $1"; }
if pg_lsclusters -h | awk '{print $4}' | grep -q online; then ok postgres; else start postgres; sudo pg_ctlcluster 17 main start; fi
if pgrep -f "[g]rafana server" >/dev/null; then ok grafana; else start grafana
  GF_SECURITY_ADMIN_PASSWORD=$GF_ADMIN_PASSWORD PGPASSWORD=$PGPASSWORD nohup /usr/share/grafana/bin/grafana server --homepath /usr/share/grafana --config grafana/grafana.ini >> metrics/grafana.out 2>&1 & fi
if pgrep -f "[r]un_listener.sh" >/dev/null; then ok listener; else start listener; nohup tools/run_listener.sh >/dev/null 2>&1 & fi
if pgrep -f "[h]ttp.server 8787" >/dev/null; then ok dashboard; else start dashboard; nohup tools/run_dashboard.sh >> metrics/dashboard.out 2>&1 & fi
