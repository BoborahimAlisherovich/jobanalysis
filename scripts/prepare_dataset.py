#!/usr/bin/env python3
"""Prepare vacancies dataset for AI: dedupe, normalize, extract skills, export JSONL/CSV."""
import argparse
import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Any

SKILLS = [
    'python','django','flask','sql','postgres','mysql','react','vue','angular','javascript',
    'java','golang','go','c++','c#','dotnet','php','ruby','rust','kubernetes','docker',
    'aws','azure','gcp','devops','ml','machine learning','data','tensorflow','pytorch',
    'flutter','swift','kotlin','android','ios','html','css','node','nodejs'
]

NUM_RE = re.compile(r"(\d[\d\s\u202f]{2,})")


def extract_numbers(text: str) -> List[int]:
    nums = []
    for m in NUM_RE.findall(text or ''):
        n = int(re.sub(r"[\s\u202f]", "", m))
        nums.append(n)
    return nums


def extract_skills(text: str) -> List[str]:
    t = (text or '').lower()
    found = set()
    for kw in SKILLS:
        if kw in t:
            found.add(kw)
    return sorted(found)


def normalize_record(item: Dict[str, Any]) -> Dict[str, Any]:
    f = item.get('fields', {})
    title = f.get('title', '')
    desc = f.get('description', '')
    text = (title + '\n' + desc).strip()
    # deduce salary from numbers >=1000
    salary_min = f.get('salary_min') or 0
    salary_max = f.get('salary_max') or 0
    # if parsed salary looks like a year (< 3000), try extract larger numbers
    if (salary_max and salary_max < 3000) or (salary_min and salary_min < 3000):
        nums = extract_numbers(text)
        nums = [n for n in nums if n >= 1000]
        if nums:
            salary_min = min(nums)
            salary_max = max(nums)

    skills = extract_skills(text)
    probable_it = bool(skills) or 'it' in (f.get('category','') or '').lower()

    return {
        'id': item.get('pk'),
        'title': title,
        'description': desc,
        'text': text,
        'skills': skills,
        'probable_it': probable_it,
        'category': f.get('category'),
        'country': f.get('country'),
        'source': f.get('source'),
        'source_url': f.get('source_url'),
        'salary_min': salary_min,
        'salary_max': salary_max,
        'currency': f.get('currency'),
        'posted_at': f.get('posted_at'),
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--input', default='data/vacancies_it.json')
    p.add_argument('--output', default='data/vacancies_it_clean.jsonl')
    p.add_argument('--csv', default='data/vacancies_it_clean.csv')
    args = p.parse_args(argv)

    inp = Path(args.input)
    if not inp.exists():
        print('Input file not found:', inp)
        return 2

    with inp.open('r', encoding='utf-8') as f:
        data = json.load(f)

    seen = set()
    records = []
    for item in data:
        fields = item.get('fields', {})
        url = fields.get('source_url')
        if not url:
            continue
        if url in seen:
            continue
        seen.add(url)
        rec = normalize_record(item)
        records.append(rec)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', encoding='utf-8') as fo:
        for r in records:
            fo.write(json.dumps(r, ensure_ascii=False) + '\n')

    # write CSV
    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open('w', encoding='utf-8', newline='') as fc:
        fieldnames = ['id','title','source','source_url','category','country','salary_min','salary_max','currency','skills','probable_it','posted_at','text']
        writer = csv.DictWriter(fc, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            row = {k: '' for k in fieldnames}
            row.update({
                'id': r.get('id',''),
                'title': r.get('title',''),
                'source': r.get('source',''),
                'source_url': r.get('source_url',''),
                'category': r.get('category',''),
                'country': r.get('country',''),
                'salary_min': r.get('salary_min',''),
                'salary_max': r.get('salary_max',''),
                'currency': r.get('currency',''),
                'skills': ','.join(r.get('skills',[])),
                'probable_it': r.get('probable_it',False),
                'posted_at': r.get('posted_at',''),
                'text': r.get('text',''),
            })
            writer.writerow(row)

    print(f'Wrote {len(records)} cleaned records to {out_path} and {csv_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
