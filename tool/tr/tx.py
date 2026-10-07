# -*- coding: utf-8 -*-
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glossary as G
import glossary2
G.WORD.update({k:v for k,v in glossary2.WORD2.items() if k not in G.WORD})
import glossary3
G.WORD.update({k:v for k,v in glossary3.WORD3.items() if k not in G.WORD})
import glossary4
G.WORD.update({k:v for k,v in glossary4.WORD4.items() if k not in G.WORD})
import glossary5
G.WORD.update(glossary5.WORD5)

import phrases1, rules, josa
import phrases2
import phrases3
HAND = dict(phrases1.P1); HAND.update(phrases2.P2); HAND.update(phrases3.P3)   # 전체 문자열 수동 번역 (최우선)

def _keys_sorted(d):
    return sorted(d.keys(), key=lambda k:-len(k.split()))

def greedy(text, unknown):
    """공백 단위 그리디 매칭. 미매칭 토큰은 unknown 에 기록하고 원문 유지."""
    words=text.split()
    out=[]; i=0
    maxlen=4
    while i<len(words):
        hit=None
        for L in range(min(maxlen,len(words)-i),0,-1):
            cand=' '.join(words[i:i+L])
            if cand in G.WORD: hit=(G.WORD[cand],L); break
            cs=cand.rstrip('.,')
            if cs in G.WORD: hit=(G.WORD[cs],L); break
        if hit:
            out.append(hit[0]); i+=hit[1]
        else:
            unknown[words[i]]=unknown.get(words[i],0)+1
            out.append(words[i]); i+=1
    return ' '.join(out)

HAND_SUFFIX=[(' 1h','(한손)'),(' 2h','(양손)')]

VERBS={"Build":"제작","Make":"제작","Craft":"제작","Deposit":"보관","Select":"선택","Deselect":"선택 해제",
"Remove":"제거","Toggle":"전환","Open":"열기","Close":"닫기","Butcher":"도축","Boil":"삶기","Roast":"굽기",
"Smelt":"제련","Burn":"태우기","Eat":"먹기","Drink":"마시기","Fill":"채우기","Harvest":"수확",
"Deconstruct":"해체","Recycle":"재활용","Equip":"장착","Train":"훈련","Summon":"소환","Write":"기록",
"Add":"추가","Set":"설정","Claim":"할당","Clear":"해제","Repair":"수리","Destroy":"파괴","Throw":"던지기",
"Track":"추적","Untrack":"추적 해제","Mine":"채굴","Cook":"조리","Plant":"심기","Extract":"추출",
"Collect":"수집","Rename":"이름 변경","Rotate":"회전","Show":"표시","Hide":"숨기기","Move":"이동",
"Load":"불러오기","Save":"저장","Start":"시작","Stop":"정지","Use":"사용","Bake":"굽기","Shear":"털 깎기",
"Incubate":"부화","Graze":"방목","Till":"갈기","Expand":"펼치기","Collapse":"접기","Duplicate":"복제",
"Delete":"삭제","Randomize":"무작위화","Settle":"정착","Trade":"거래","Ignite":"점화","Sell":"판매",
"Buy":"구매","Assign":"배정","Unassign":"배정 해제","Sort":"정렬","Filter":"필터","Cancel":"취소",
"Confirm":"확인","Apply":"적용","Reset":"초기화","Zoom":"확대/축소","Pan":"화면 이동","Increase":"증가",
"Decrease":"감소","Enable":"활성화","Disable":"비활성화","Lock":"잠금","Unlock":"잠금 해제"}

import re as _re
def _dedup(t):
    t=_re.sub(r'(버섯)\s*버섯', r'\1', t)
    t=_re.sub(r'(나무)\s*나무', r'\1', t)
    return t

def translate(s, unknown=None):
    return _dedup(josa.fix(_translate(s, unknown)))

def _translate(s, unknown=None):
    if unknown is None: unknown={}
    s0=s.strip()
    if s0 in HAND: return HAND[s0]
    if s0 in G.PHRASE: return G.PHRASE[s0]
    suf=''
    for a,b in HAND_SUFFIX:
        if s0.endswith(a): s0=s0[:-len(a)]; suf=b; break
    if s0 in HAND: return HAND[s0]+suf
    if s0 in G.PHRASE: return G.PHRASE[s0]+suf
    # 괄호 처리
    m=re.match(r'^(.*?)\s*\((.*)\)$', s0)
    if m:
        return _translate(m.group(1),unknown)+' ('+_translate(m.group(2),unknown)+')'+suf
    if s0.startswith('on ') and s0[3:] in rules.ON: return rules.ON[s0[3:]]+suf
    m=re.match(r'^Set Timescale to (\d)x$', s0)
    if m: return '시간 배속 %s배'%m.group(1)
    for pat,fmt in rules.PATTERNS:
        if fmt is None: continue
        m=re.match(pat, s0)
        if m:
            parts=[_translate(g,unknown) for g in m.groups()]
            return fmt.format(*parts)+suf
    w=s0.split()
    if len(w)>1 and w[0] in VERBS:
        rest=' '.join(w[1:])
        rt = HAND.get(rest) or G.PHRASE.get(rest) or greedy(rest, unknown)
        return (rt+suf+' '+VERBS[w[0]]).strip()
    return greedy(s0, unknown)+suf

def coverage(strings):
    unknown={}
    res={s:translate(s,unknown) for s in strings}
    untouched=[s for s,t in res.items() if t==s]
    return res, unknown, untouched
