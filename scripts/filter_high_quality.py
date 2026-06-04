#!/usr/bin/env python3
"""Filter cleaned vacancies to high-quality IT records for training."""
import json
from pathlib import Path
from typing import Set

GOOD_SOURCES = {'kwork.ru','apwork.uz','hh.uz','linkedin','linkedin.com'}
KEYWORDS = set([
    'python','django','flask','sql','postgres','mysql','react','vue','angular','javascript',
    'java','go','golang','c++','c#','php','ruby','rust','kubernetes','docker','aws','azure',
    'gcp','devops','ml','machine learning','data','tensorflow','pytorch','flutter','android','ios'
])


def has_keyword(text: str, kws: Set[str]) -> bool:
    t = (text or '').lower()
    for k in kws:
        if k in t:
            return True
    return False


def main():
    inp = Path('data/vacancies_it_clean.jsonl')
    out = Path('data/vacancies_it_train.jsonl')
    if not inp.exists():
        print('Cleaned input not found:', inp)
        return 2

    out.parent.mkdir(parents=True, exist_ok=True)
    kept = 0
    total = 0
    with inp.open('r', encoding='utf-8') as fi, out.open('w', encoding='utf-8') as fo:
        for line in fi:
            total += 1
            r = json.loads(line)
            text = r.get('text','')
            skills = r.get('skills',[])
            src = (r.get('source') or '').lower()
            keep = False
            if skills:
                keep = True
            if src in GOOD_SOURCES:
                keep = True
            if has_keyword(text, KEYWORDS):
                keep = True
            if keep:
                fo.write(json.dumps(r, ensure_ascii=False) + '\n')
                kept += 1

    print(f'Filtered {kept}/{total} records to {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
