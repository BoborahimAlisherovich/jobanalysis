#!/usr/bin/env python3
"""Fetch vacancies from an API and export as Django fixture JSON.

Usage:
  python scripts/fetch_vacancies.py --url "https://api.example.com/vacancies" \
    --model jobs.vacancy --id-field id --output data/vacancies.json

The script follows pagination if the API returns JSON with `results` and `next`.
"""
import argparse
import json
import sys
from typing import Any, Dict, List, Optional

import requests


def fetch_all(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    while url:
        resp = requests.get(url, headers=headers or {}, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            if 'results' in data and isinstance(data['results'], list):
                items.extend(data['results'])
                url = data.get('next')
            else:
                # try common container keys
                for k in ('data', 'items', 'vacancies', 'results'):
                    if k in data and isinstance(data[k], list):
                        items.extend(data[k])
                        url = None
                        break
                else:
                    # single object -> append once
                    items.append(data)
                    url = None
        elif isinstance(data, list):
            items.extend(data)
            url = None
        else:
            # unknown shape
            items.append({'value': data})
            url = None
    return items


def to_fixture(items: List[Dict[str, Any]], model: str, id_field: str) -> List[Dict[str, Any]]:
    fixtures: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        pk = item.get(id_field)
        fields = {k: v for k, v in item.items() if k != id_field}
        fixtures.append({
            'model': model,
            'pk': pk,
            'fields': fields,
        })
    return fixtures


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description='Fetch vacancies and export Django fixture JSON')
    p.add_argument('--url', required=True, help='API URL to fetch (can be paginated)')
    p.add_argument('--model', required=True, help='Django model name for fixtures, e.g. jobs.vacancy')
    p.add_argument('--id-field', default='id', help='Field to use as primary key (default: id)')
    p.add_argument('--output', default='vacancies.json', help='Output JSON filepath')
    p.add_argument('--header', action='append', help='Optional header in Key:Value form, repeatable')
    args = p.parse_args(argv)

    headers = {}
    if args.header:
        for h in args.header:
            if ':' in h:
                k, v = h.split(':', 1)
                headers[k.strip()] = v.strip()

    try:
        items = fetch_all(args.url, headers=headers)
    except requests.RequestException as e:
        print('Request failed:', e, file=sys.stderr)
        return 2

    fixtures = to_fixture(items, args.model, args.id_field)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(fixtures, f, ensure_ascii=False, indent=2)

    print(f'Wrote {len(fixtures)} fixture records to {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
