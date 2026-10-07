# -*- coding: utf-8 -*-
"""Go 설치기(exe) 빌드 — Go 가 없으면 건너뛴다."""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import orpaths

VERSION = '1.0.3'
GODIR = os.path.join(orpaths.TOOL, 'dist_patcher', 'go')


def main():
    go = shutil.which('go')
    if not go:
        print('Go 가 설치되어 있지 않아 exe 빌드를 건너뜁니다.')
        print('스크립트판(zip)만으로도 배포에는 문제가 없습니다.')
        print('exe 도 만들려면 https://go.dev/dl/ 에서 Go 를 설치하세요.')
        return

    orkp = os.path.join(orpaths.OUT, 'build', 'patch.orkp')
    if not os.path.exists(orkp):
        raise SystemExit('patch.orkp 가 없습니다. 먼저 dist_gen/mkdelta.py 를 실행하세요.')
    # go:embed 는 소스와 같은 폴더의 파일만 읽는다
    shutil.copy2(orkp, os.path.join(GODIR, 'patch.orkp'))

    dst = os.path.join(orpaths.out('dist'), 'OddRealm_한글패치_v%s.exe' % VERSION)
    env = dict(os.environ, GOOS='windows', GOARCH='amd64', CGO_ENABLED='0')
    # -ldflags="-s -w" 는 쓰지 않는다. 심볼을 지운 바이너리가 백신 오탐을 더 잘 받는다.
    r = subprocess.run([go, 'build', '-trimpath', '-o', dst, '.'], cwd=GODIR, env=env)
    if r.returncode != 0:
        raise SystemExit('go build 실패')
    print('exe  :', dst, '(%,d bytes)'.replace('%,d', '{:,}'.format(os.path.getsize(dst))))


if __name__ == '__main__':
    main()
