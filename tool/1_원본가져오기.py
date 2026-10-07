# -*- coding: utf-8 -*-
"""게임 폴더에서 패치 대상 원본 5개 파일을 original/ 로 복사한다.

이미 한글패치가 적용된 상태라면 게임 폴더의 _KoreanPatch_Backup 안에서
원본을 찾아 가져온다. 그래도 없으면 Steam 파일 무결성 검사를 안내한다.
"""
import orpaths
import os
import shutil

def find_original(game, key):
    """원본 SHA-256 과 일치하는 파일을 찾아 경로를 돌려준다."""
    want = orpaths.SHA[key]
    live = os.path.join(game, orpaths.REL[key].replace('/', os.sep))
    if os.path.exists(live) and orpaths.sha256(live) == want:
        return live, '게임 폴더'
    name = os.path.basename(orpaths.REL[key])
    broot = os.path.join(game, '_KoreanPatch_Backup')
    if os.path.isdir(broot):
        for sub in sorted(os.listdir(broot)):
            cand = os.path.join(broot, sub, name)
            if os.path.exists(cand) and orpaths.sha256(cand) == want:
                return cand, '백업 폴더(%s)' % sub
    return None, None


def main():
    game = orpaths.game_dir()
    print('게임 폴더:', game)
    os.makedirs(orpaths.ORIGINAL, exist_ok=True)

    missing = []
    for key in orpaths.ORDER:
        name = os.path.basename(orpaths.REL[key])
        dst = os.path.join(orpaths.ORIGINAL, name)
        if os.path.exists(dst) and orpaths.sha256(dst) == orpaths.SHA[key]:
            print('  %-46s 이미 있음' % name)
            continue
        srcp, where = find_original(game, key)
        if srcp is None:
            print('  %-46s 원본을 찾지 못함' % name)
            missing.append(name)
            continue
        shutil.copy2(srcp, dst)
        print('  %-46s 복사 완료  <- %s' % (name, where))

    if missing:
        print()
        print('아래 파일의 원본을 찾지 못했습니다:')
        for m in missing:
            print('   -', m)
        print()
        print('Steam → Odd Realm 우클릭 → 속성 → 설치된 파일 → 파일 무결성 검사')
        print('를 돌려 원본으로 되돌린 뒤 이 스크립트를 다시 실행해 주세요.')
        print('(게임이 업데이트되어 빌드가 바뀐 경우라면 orpaths.py 의 SHA 값을 갱신해야 합니다.)')
        raise SystemExit(1)

    print()
    print('원본 5개 파일이 original/ 에 준비되었습니다.')

if __name__ == '__main__':
    main()
