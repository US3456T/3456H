#!/usr/bin/env bash
set -e

case "${1:-up}" in
  up)
    docker compose up --build "${@:2}"
    ;;
  down)
    docker compose down
    ;;
  logs)
    docker compose logs -f "${@:2}"
    ;;
  *)
    echo "用法：./build_and_run.sh up|down|logs"
    exit 1
    ;;
esac
