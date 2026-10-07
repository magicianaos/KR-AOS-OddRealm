# -*- coding: utf-8 -*-
"""직접 교체용 zip 생성 — 실행 파일이 전혀 없는 배포본.

이미 번역이 적용된 게임 파일 5개를 게임 폴더 구조 그대로 담는다.
사용자는 압축을 풀어 게임 폴더에 덮어쓰기만 하면 된다.
"""
import os
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import orpaths

VERSION = '1.0.3'

README = '''================================================================
  Odd Realm 한글패치 v{ver}  (직접 교체용)
================================================================

프로그램을 실행하지 않고, 파일만 덮어쓰는 방식입니다.


■ 설치 방법

  1. 게임 폴더를 엽니다.
     Steam 라이브러리 -> Odd Realm 우클릭 -> 관리 -> 로컬 파일 보기

     보통 여기입니다.
       C:\\Program Files (x86)\\Steam\\steamapps\\common\\Odd Realm

  2. 이 압축 안의 "OddRealm_Data" 폴더를 게임 폴더에 끌어다 놓습니다.

  3. "대상 폴더에 같은 이름의 파일이 있습니다" 라고 물어보면
     [파일 덮어쓰기] 를 선택합니다.

  4. 게임을 실행합니다.

  ※ 게임이 실행 중이면 먼저 종료해 주세요.
  ※ 덮어쓰기가 막히면 게임 폴더를 관리자 권한으로 열거나,
     Steam 을 종료한 뒤 다시 시도해 주세요.


■ 원래대로 되돌리기

  Steam -> Odd Realm 우클릭 -> 속성 -> 설치된 파일 -> 파일 무결성 검사

  바뀐 파일만 자동으로 다시 받아서 영어 원본으로 돌아갑니다.
  세이브 파일은 지워지지 않습니다.


■ 지원 게임 버전

  build-guid  b0f6624f52e44a52af4894850d5d2a26   (v1.1.0 darkest depths)

  ※ 이 방식은 버전을 자동으로 확인하지 않습니다.
     게임이 업데이트된 뒤에 덮어쓰면 게임이 실행되지 않을 수 있습니다.
     그럴 때는 위의 파일 무결성 검사로 되돌리시면 됩니다.

     버전 확인과 자동 백업까지 해 주는 설치기 버전도 함께 배포하고 있습니다.
     그쪽이 더 안전합니다.


■ 무엇이 한글화되나요

  아이템 / 건물 / 작업 / 직업 / 기술 / 능력치 / 종족 / 상태이상
  툴팁 설명문 / NPC 대사 / 튜토리얼          10,329곳
  메뉴 / 버튼 / 설정 / 알림 / 개체 정보창         943개

  게임 원본 폰트에 한글이 없어서 한글 폰트를 새로 만들어 넣었습니다.
  완성형 11,172자 전체 + 호환 자모 + 한국어 문장부호


■ 폰트

  Galmuri11  Copyright (c) 2019-2025 Lee Minseo (quiple@quiple.dev)
  SIL Open Font License 1.1
  https://github.com/quiple/galmuri


■ 제작

  {author}

================================================================
'''


def main():
    out_dir = orpaths.out('dist')
    stage = os.path.join(orpaths.OUT, '_direct')
    shutil.rmtree(stage, ignore_errors=True)

    built = {
        'tooltips':        os.path.join(orpaths.OUT, 'patch', 'defaultlocalgroup_assets_tooltips.bundle'),
        'dialogue':        os.path.join(orpaths.OUT, 'patch', 'defaultlocalgroup_assets_dialogue.bundle'),
        'tutorialsegment': os.path.join(orpaths.OUT, 'patch', 'defaultlocalgroup_assets_tutorialsegment.bundle'),
        'resources':       os.path.join(orpaths.OUT, 'resources.assets'),
        'metadata':        os.path.join(orpaths.OUT, 'patch_meta', 'global-metadata.dat'),
    }
    for k, p in built.items():
        if not os.path.exists(p):
            raise SystemExit('%s 가 없습니다. 먼저 2_빌드.py 를 실행하세요.' % p)
        dst = os.path.join(stage, orpaths.REL[k].replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(p, dst)

    author = '(제작자 표기 자리)'
    txt = README.format(ver=VERSION, author=author).replace('\r\n', '\n').replace('\n', '\r\n')
    with open(os.path.join(stage, '읽어주세요.txt'), 'wb') as f:
        f.write(b'\xef\xbb\xbf' + txt.encode('utf-8'))

    zpath = os.path.join(out_dir, 'OddRealm_한글패치_v%s_직접교체용.zip' % VERSION)
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for base, _d, files in os.walk(stage):
            for f in sorted(files):
                full = os.path.join(base, f)
                z.write(full, os.path.relpath(full, stage))
    shutil.rmtree(stage, ignore_errors=True)
    print('직접교체용 zip :', zpath, '({:,} bytes)'.format(os.path.getsize(zpath)))


if __name__ == '__main__':
    main()
