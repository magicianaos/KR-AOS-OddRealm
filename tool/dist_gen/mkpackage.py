# -*- coding: utf-8 -*-
"""배포 zip 생성 — 스크립트판(exe 없음)."""
import os
import sys
import shutil
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import orpaths

VERSION = '1.0.3'
PSDIR = os.path.join(orpaths.TOOL, 'dist_patcher', 'ps')


def bom_crlf(src, dst):
    s = open(src, encoding='utf-8').read().replace('\r\n', '\n').replace('\n', '\r\n')
    open(dst, 'wb').write(b'\xef\xbb\xbf' + s.encode('utf-8'))


def main():
    orkp = os.path.join(orpaths.OUT, 'build', 'patch.orkp')
    if not os.path.exists(orkp):
        raise SystemExit('patch.orkp 가 없습니다. 먼저 dist_gen/mkdelta.py 를 실행하세요.')

    root = orpaths.out('dist')
    name = 'OddRealm 한글패치 v%s (스크립트판)' % VERSION
    pkg = os.path.join(root, name)
    if os.path.isdir(pkg):
        shutil.rmtree(pkg)
    os.makedirs(os.path.join(pkg, '라이선스'))

    shutil.copy2(orkp, os.path.join(pkg, 'patch.orkp'))
    # .bat 런처는 넣지 않는다. bat 이 powershell 을 우회 옵션으로 부르는 형태가
    # 악성 다운로더와 동일해서 클라우드 저장소·백신이 오탐한다. (v1.0.3)
    # .ps1 / .txt 는 UTF-8 BOM 필수 (Windows PowerShell 5.1 이 BOM 없으면 ANSI 로 읽는다)
    bom_crlf(os.path.join(PSDIR, '한글패치_설치.ps1'), os.path.join(pkg, '한글패치_설치.ps1'))
    bom_crlf(os.path.join(PSDIR, '읽어보세요.txt'), os.path.join(pkg, '읽어보세요.txt'))
    shutil.copy2(os.path.join(orpaths.TOOL, 'font', 'OFL-Galmuri.txt'),
                 os.path.join(pkg, '라이선스', 'OFL-Galmuri.txt'))

    zpath = os.path.join(root, 'OddRealm_한글패치_v%s_스크립트판.zip' % VERSION)
    # zipfile 은 비ASCII 이름에 UTF-8 플래그(bit 11)를 세워준다. 윈도우 탐색기 호환.
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for base, _dirs, files in os.walk(pkg):
            for f in sorted(files):
                full = os.path.join(base, f)
                z.write(full, os.path.join(name, os.path.relpath(full, pkg)))

    print('폴더 :', pkg)
    print('zip  :', zpath, '(%,d bytes)'.replace('%,d', '{:,}'.format(os.path.getsize(zpath))))


if __name__ == '__main__':
    main()
