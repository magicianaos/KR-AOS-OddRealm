#!/usr/bin/env python3
"""ORKP1 델타 생성기 — 원본/패치본 쌍에서 COPY/INSERT 스트림을 만든다."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import orpaths
import hashlib, struct, zlib

BLK = 32          # 블록 해시 크기
MINMATCH = 32

def build_index(src):
    idx = {}
    for i in range(0, len(src) - BLK + 1, BLK):
        idx.setdefault(src[i:i+BLK], i)
    return idx

def delta(src, dst):
    idx = build_index(src)
    ops = []            # (kind, a, b)  kind 1=COPY(off,len) 2=INSERT(start,end)
    lit = 0
    i = 0
    n = len(dst)
    while i < n:
        m = None
        if i + BLK <= n:
            cand = idx.get(dst[i:i+BLK])
            if cand is not None:
                # 뒤로 확장
                e = BLK
                while (i + e < n and cand + e < len(src)
                       and dst[i+e] == src[cand+e]):
                    e += 1
                # 앞으로 확장 (리터럴 잡아먹기)
                s = 0
                while (s < i - lit and cand - s - 1 >= 0
                       and dst[i-s-1] == src[cand-s-1]):
                    s += 1
                if e + s >= MINMATCH:
                    m = (cand - s, e + s, i - s)
        if m is None:
            i += 1
            continue
        srcoff, mlen, start = m
        if start > lit:
            ops.append((2, lit, start))
        ops.append((1, srcoff, mlen))
        i = start + mlen
        lit = i
    if lit < n:
        ops.append((2, lit, n))
    return ops

def encode(src, dst, ops):
    out = bytearray()
    out += struct.pack('<I', len(ops))
    for kind, a, b in ops:
        if kind == 1:
            out += struct.pack('<BQI', 1, a, b)
        else:
            chunk = dst[a:b]
            out += struct.pack('<BI', 2, len(chunk)) + chunk
    return bytes(out)

def make(pairs):
    """pairs: [(relpath, src_path, dst_path)] -> bytes"""
    body = bytearray()
    body += struct.pack('<I', len(pairs))
    for rel, sp, dp in pairs:
        src = open(sp, 'rb').read()
        dst = open(dp, 'rb').read()
        ops = delta(src, dst)
        blob = encode(src, dst, ops)
        ins = sum(b - a for k, a, b in ops if k == 2)
        rb = rel.encode('utf8')
        body += struct.pack('<H', len(rb)) + rb
        body += hashlib.sha256(src).digest()
        body += hashlib.sha256(dst).digest()
        body += struct.pack('<QQ', len(src), len(dst))
        body += struct.pack('<I', len(blob)) + blob
        print(f'  {rel:70s} {len(src):>10,} -> {len(dst):>10,}  ops {len(ops):>6,}  insert {ins:>10,}')
    comp = zlib.compress(bytes(body), 9)
    return b'ORKP1\x00\x00\x00' + struct.pack('<Q', len(body)) + comp

if __name__ == '__main__':
    OUT = orpaths.OUT
    pairs = [
        (orpaths.REL['tooltips'],        orpaths.src('tooltips'),
         os.path.join(OUT, 'patch', 'defaultlocalgroup_assets_tooltips.bundle')),
        (orpaths.REL['dialogue'],        orpaths.src('dialogue'),
         os.path.join(OUT, 'patch', 'defaultlocalgroup_assets_dialogue.bundle')),
        (orpaths.REL['tutorialsegment'], orpaths.src('tutorialsegment'),
         os.path.join(OUT, 'patch', 'defaultlocalgroup_assets_tutorialsegment.bundle')),
        (orpaths.REL['resources'],       orpaths.src('resources'),
         os.path.join(OUT, 'resources.assets')),
        (orpaths.REL['metadata'],        orpaths.src('metadata'),
         os.path.join(OUT, 'patch_meta', 'global-metadata.dat')),
    ]
    data = make(pairs)
    dst = orpaths.out('build', 'patch.orkp')
    open(dst, 'wb').write(data)
    print('patch.orkp', f'{len(data):,} bytes ->', dst)
