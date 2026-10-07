# -*- coding: utf-8 -*-
import re
def _jong(ch):
    o=ord(ch)
    if 0xAC00<=o<=0xD7A3: return (o-0xAC00)%28
    return None
DIGIT_JONG={'0':8,'1':0,'3':0,'6':0,'7':8,'8':0,'2':0,'4':0,'5':0,'9':0}
def has_batchim(s):
    s=re.sub(r'[\)\]\}\s\.\!\?]+$','',s)
    if not s: return False
    ch=s[-1]
    j=_jong(ch)
    if j is not None: return (j, j==8)   # (종성코드, ㄹ여부)
    if ch.isdigit(): return (DIGIT_JONG.get(ch,0), ch in '17')
    if ch.isalpha(): return (1, False)   # 영문은 받침 있는 것으로 처리
    return (0, False)
def fix(text):
    def rep(m):
        head=m.group(1); form=m.group(2)
        st=has_batchim(head)
        j,is_r = st if isinstance(st,tuple) else (0,False)
        if form=='(으)로': tail='로' if (j==0 or is_r) else '으로'
        elif form=='을(를)': tail='을' if j else '를'
        elif form=='이(가)': tail='이' if j else '가'
        elif form=='은(는)': tail='은' if j else '는'
        elif form=='와(과)': tail='와' if not j else '과'
        elif form=='이(가) ': tail=('이 ' if j else '가 ')
        else: tail=form
        return head+tail
    return re.sub(r'(\S)\s*(\(으\)로|을\(를\)|이\(가\)|은\(는\)|와\(과\))', lambda m: rep(m), text)
