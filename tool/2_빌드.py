# -*- coding: utf-8 -*-
"""전체 빌드: 번들 → 폰트/리소스 → 메타데이터 → 델타 → 배포 zip."""
import orpaths
import os
import subprocess
import sys
import time

TOOL = orpaths.TOOL
STEPS = [
    ('번역 번들 3종 빌드',        [sys.executable, os.path.join(TOOL, 'build_all.py')]),
    ('한글 폰트 + resources 빌드', [sys.executable, os.path.join(TOOL, 'buildko.py')]),
    ('UI 메타데이터 패치',        [sys.executable, os.path.join(TOOL, 'metapatch.py')]),
    ('ORKP1 델타 생성',           [sys.executable, os.path.join(TOOL, 'dist_gen', 'mkdelta.py')]),
    ('설치기 exe 빌드',           [sys.executable, os.path.join(TOOL, 'dist_gen', 'mkexe.py')]),
    ('배포 패키지 생성',          [sys.executable, os.path.join(TOOL, 'dist_gen', 'mkpackage.py')]),
    ('직접 교체용 zip 생성',      [sys.executable, os.path.join(TOOL, 'dist_gen', 'mkdirect.py')]),
]

def main():
    if not os.path.isdir(orpaths.ORIGINAL) or not os.listdir(orpaths.ORIGINAL):
        print('original/ 이 비어 있습니다. 먼저 1_원본가져오기.py 를 실행해 주세요.')
        raise SystemExit(1)
    t0 = time.time()
    for i, (label, cmd) in enumerate(STEPS, 1):
        print()
        print('=' * 62)
        print('[%d/%d] %s' % (i, len(STEPS), label))
        print('=' * 62)
        r = subprocess.run(cmd, cwd=TOOL)
        if r.returncode != 0:
            print()
            print('[중단] %s 단계에서 실패했습니다.' % label)
            raise SystemExit(r.returncode)
    print()
    print('전체 빌드 완료 (%.1f초)' % (time.time() - t0))
    print('배포물:', os.path.join(orpaths.OUT, 'dist'))

if __name__ == '__main__':
    main()
