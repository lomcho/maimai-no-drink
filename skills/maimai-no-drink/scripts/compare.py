"""Compare normalized quotes, never call orders or infer official API fields."""
import json
import sys
from datetime import datetime, timezone


def rank(request, quotes, now=None):
    now = now or datetime.now(timezone.utc)
    drink_mode = request.get('drink_mode', 'exclude')
    if drink_mode not in ('indifferent', 'exclude'):
        raise ValueError('Unsupported drink mode')
    if not request['required'] or any(type(v) is not int or v <= 0 for v in request['required'].values()):
        raise ValueError('Invalid required quantities')
    accepted, rejected, seen = [], [], set()
    if not quotes:
        return {'source': None, 'best': None, 'no_drink': None, 'no_drink_extra_fen': None,
                'rejected': [], 'scope': 'no quotes available'}
    if any(not isinstance(q, dict) for q in quotes):
        raise ValueError('Quotes must be objects')
    ids = [q.get('id') for q in quotes]
    if any(not isinstance(x, str) or not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError('Quote ids must be nonempty and unique')
    sources = {q.get('source') for q in quotes}
    if len(sources) != 1 or not sources <= {'live', 'simulation'}:
        raise ValueError('One explicit source mode is required')
    for q in quotes:
        reason = None
        try:
            if q['id'] in seen:
                raise ValueError('duplicate id')
            seen.add(q['id'])
            if q['context'] != request['context']:
                raise ValueError('different context')
            if q['confirmed'] is not True or q['fees_complete'] is not True:
                raise ValueError('unconfirmed price or incomplete fees')
            if type(q['payable_fen']) is not int or q['payable_fen'] < 0:
                raise ValueError('invalid amount')
            if type(q['drinks']) is not int or q['drinks'] < 0:
                raise ValueError('invalid drinks')
            if not isinstance(q['foods'], dict) or any(type(v) is not int or v < 0 for v in q['foods'].values()):
                raise ValueError('invalid food quantities')
            if any(q['foods'].get(k, 0) < v for k, v in request['required'].items()):
                raise ValueError('required food quantity mismatch')
            if not request.get('allow_extra_food', False) and any(v != request['required'].get(k, 0) for k,v in q['foods'].items()):
                raise ValueError('extra food not authorized')
            if not isinstance(q['resources'], list) or not set(q['resources']) <= set(request.get('allow_resources', [])):
                raise ValueError('resource not authorized')
            stamp = datetime.fromisoformat(q['quoted_at'])
            if stamp.tzinfo is None or not 0 <= (now - stamp).total_seconds() <= 600:
                raise ValueError('stale or invalid quote time')
            if drink_mode == 'exclude' and q['drinks']:
                raise ValueError('beverage excluded')
        except (KeyError, TypeError, ValueError) as e:
            reason = str(e)
        if reason:
            rejected.append({'id': q.get('id'), 'reason': reason})
        else:
            accepted.append(q)
    accepted.sort(key=lambda q: (q['payable_fen'], q['drinks'], q['id']))
    best = accepted[0] if accepted else None
    dry = next((q for q in accepted if q['drinks'] == 0), None)
    return {'source': next(iter(sources)), 'best': best, 'no_drink': dry,
            'no_drink_extra_fen': dry['payable_fen'] - best['payable_fen'] if dry and best else None,
            'rejected': rejected, 'scope': 'submitted verified candidates only'}


if __name__ == '__main__':
    with open(sys.argv[1], encoding='utf-8-sig') as stream:
        data = json.load(stream)
    print(json.dumps(rank(data['request'], data['quotes']), ensure_ascii=False, indent=2))
