  1
  2
  3
  4
  5
  6
  7
  8
  9
 10
 11
 12
 13
 14
 15
 16
 17
 18
 19
 20
 21
 22
 23
#!/usr/bin/env bash
CMD="$1"
if [ -z "$CMD" ]; then
  echo "用法: $0 up|down|logs"
  exit 1
fi

case "$CMD" in
  up)
    docker-compose up --build ${@:2}
    ;;
  down)
    docker-compose down
    ;;
  logs)
    docker-compose logs -f ${@:2}
    ;;
  *)
    echo "未知命令: $CMD"
    echo "用法: $0 up|down|logs"
    exit 2
    ;;
esac