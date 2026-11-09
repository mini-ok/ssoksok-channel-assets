#!/usr/bin/env bash
# Code Animation 작업 환경 준비 (Ubuntu/Claude 클라우드 세션 기준)
set -e
REPO=${REPO:-https://github.com/mini-ok/ssoksok-channel-assets}
cd /home/claude 2>/dev/null || cd ~
[ -d ssoksok-channel-assets ] || git clone "$REPO"
CA="$PWD/ssoksok-channel-assets/Code Animation"
# 1) 시스템 도구: ffmpeg, cairo, CJK 폰트
sudo apt-get update -y && sudo apt-get install -y ffmpeg libcairo2-dev pkg-config fonts-noto-cjk || true
# 2) 파이썬 패키지
pip install -r "$(dirname "$0")/requirements.txt" --break-system-packages
# 3) three.js (숨비 3D)  — Playwright Chromium은 클라우드 세션에 이미 설치돼 있으면 생략
(cd "$CA/sumbi/three" && npm install three@0.160.0)
python3 -m playwright install chromium 2>/dev/null || true
# 4) 원래 작업 경로로 링크 (스크립트 일부가 /home/claude/<작품> 절대경로 사용)
for d in orbit keeper holssi scarecrow sumbi; do [ -e /home/claude/$d ] || ln -s "$CA/$d" /home/claude/$d; done
echo "OK: $CA"
