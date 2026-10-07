# -*- coding: utf-8 -*-
"""Odd Realm 한글화 툴킷 — 공통 경로 설정.

모든 스크립트는 맨 위에서 `import orpaths` 만 하면 된다.
sys.path 에 툴킷 루트와 tr/ 을 넣어주고, 원본 파일 위치를 찾아준다.

원본 파일을 찾는 순서
  1. <툴킷>/original/  (1_원본가져오기.py 가 채워 넣는다 — 권장)
  2. 게임 폴더        (game_path.txt → 환경변수 ODDREALM_DIR → Steam 기본 경로)
"""
import os
import sys
import hashlib

TOOL = os.path.dirname(os.path.abspath(__file__))
for _p in (TOOL, os.path.join(TOOL, 'tr')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

ORIGINAL = os.path.join(TOOL, 'original')
OUT      = os.path.join(TOOL, 'out')
FONT_TTF = os.path.join(TOOL, 'font', 'Galmuri11.ttf')
BUILD    = os.path.join(TOOL, 'out', 'build')

# 패치 대상 5개 파일 (게임 폴더 기준 상대 경로)
REL = {
    'tooltips':        'OddRealm_Data/StreamingAssets/GameData/defaultlocalgroup_assets_tooltips.bundle',
    'dialogue':        'OddRealm_Data/StreamingAssets/GameData/defaultlocalgroup_assets_dialogue.bundle',
    'tutorialsegment': 'OddRealm_Data/StreamingAssets/GameData/defaultlocalgroup_assets_tutorialsegment.bundle',
    'resources':       'OddRealm_Data/resources.assets',
    'metadata':        'OddRealm_Data/il2cpp_data/Metadata/global-metadata.dat',
}

# 지원 빌드(build-guid b0f6624f52e44a52af4894850d5d2a26)의 원본 SHA-256
SHA = {
    'tooltips':        '2e917d814ae44aaef94fa207bfef1225c8c04c8338ac7a82a17c67a3f690ad05',
    'dialogue':        '46819c4bd03a76fc23860893068c58bf303139a28cb58bd0681526f34235cc50',
    'tutorialsegment': '33c55130fd121931dc1aea828494192a402f34cac08ba851c9836f3bad85f998',
    'resources':       'f4fedd133847d6560bb719fde60fdd3dd6cd538c272d228724219f34e810b7cb',
    'metadata':        '9005fdde1639ae2166d424c2f78cde00193cefc34b67666d3eda11767770c119',
}

ORDER = ['tooltips', 'dialogue', 'tutorialsegment', 'resources', 'metadata']


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _looks_like_game(d):
    return bool(d) and (os.path.exists(os.path.join(d, 'OddRealm.exe'))
                        or os.path.isdir(os.path.join(d, 'OddRealm_Data')))


def _steam_candidates():
    out = []
    txt = os.path.join(TOOL, 'game_path.txt')
    if os.path.exists(txt):
        for line in open(txt, encoding='utf-8'):
            line = line.split('#')[0].strip().strip('"')
            if line:
                out.append(line)
    env = os.environ.get('ODDREALM_DIR')
    if env:
        out.append(env)
    bases = [r'C:\Program Files (x86)\Steam', r'C:\Program Files\Steam', r'C:\Steam']
    for d in 'DEFGHIJKL':
        bases += [d + r':\Steam', d + r':\SteamLibrary', d + r':\Program Files (x86)\Steam']
    for b in bases:
        out.append(os.path.join(b, 'steamapps', 'common', 'Odd Realm'))
        vdf = os.path.join(b, 'steamapps', 'libraryfolders.vdf')
        if os.path.exists(vdf):
            try:
                for line in open(vdf, encoding='utf-8', errors='replace'):
                    t = line.strip()
                    if t.startswith('"path"'):
                        parts = t.split('"')
                        if len(parts) >= 4:
                            out.append(os.path.join(parts[3].replace('\\\\', '\\'),
                                                    'steamapps', 'common', 'Odd Realm'))
            except OSError:
                pass
    return out


_game_cache = []


def game_dir(required=True):
    """게임 설치 폴더. 못 찾으면 None(또는 예외)."""
    if _game_cache:
        return _game_cache[0]
    for c in _steam_candidates():
        if _looks_like_game(c):
            _game_cache.append(c)
            return c
    if required:
        raise SystemExit(
            'Odd Realm 설치 폴더를 찾지 못했습니다.\n'
            '   툴킷 폴더의 game_path.txt 에 게임 폴더 경로를 한 줄로 적어 주세요.\n'
            '   예) C:\\Program Files (x86)\\Steam\\steamapps\\common\\Odd Realm')
    return None


def src(key):
    """원본 파일 경로. original/ 을 우선 사용한다."""
    name = os.path.basename(REL[key])
    p = os.path.join(ORIGINAL, name)
    if os.path.exists(p):
        return p
    g = game_dir()
    p = os.path.join(g, REL[key].replace('/', os.sep))
    if not os.path.exists(p):
        raise SystemExit('원본 파일이 없습니다: %s' % p)
    return p


def out(*parts):
    """out/ 아래 경로를 만들고 돌려준다."""
    p = os.path.join(OUT, *parts)
    d = p if not os.path.splitext(p)[1] else os.path.dirname(p)
    if d:
        os.makedirs(d, exist_ok=True)
    return p


# 자주 쓰는 별칭
def base_dir():
    """GameData 번들 폴더 (original/ 이 있으면 그쪽)."""
    return os.path.dirname(src('tooltips'))
