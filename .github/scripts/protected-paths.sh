#!/usr/bin/env bash
# stdin: GitHub PR files API의 "status<TAB>filename<TAB>previous_filename" 줄 목록
# 보호 경로를 건드린 파일이 있으면 출력하고 exit 1
set -euo pipefail

is_protected() {
  case "$1" in
    .github/* | pyproject.toml | requirements.txt | requirements-dev.txt | \
      CLAUDE.md | alembic.ini | alembic/env.py | alembic/script.py.mako)
      return 0 ;;
  esac
  return 1
}

violations=()
while IFS=$'\t' read -r status filename previous; do
  [ -n "$filename" ] || continue
  for path in "$filename" "$previous"; do
    [ -n "$path" ] || continue
    if is_protected "$path"; then
      violations+=("$status $path")
    elif [[ "$path" == alembic/versions/* && "$status" != added ]]; then
      # 새 migration 추가는 허용하고, 이미 있는 migration 수정·삭제·이름 변경만 막는다
      violations+=("$status $path")
    fi
  done
done

if [ ${#violations[@]} -eq 0 ]; then
  echo "보호 경로 변경 없음"
  exit 0
fi

echo "보호 경로를 변경한 파일:"
printf '  %s\n' "${violations[@]}"
exit 1
