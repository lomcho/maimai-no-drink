"""Offline historical replay; never a live price lookup."""
import json,sys
from pathlib import Path
from datetime import datetime
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'skills/maimai-no-drink/scripts'))
from compare import rank
from price_guard import verify_price

def replay():
    snapshot=json.loads((root/'examples/live-snapshot.json').read_text(encoding='utf-8'))
    out={'mode':'historical_replay','queried_at':snapshot['queried_at'],'results':[]}
    for group in snapshot['groups']:
        quotes=[]
        for q in group['quotes']:
            clean=verify_price(q.pop('response'))
            quotes.append({**q,**clean,'context':'historical-store-delivery','confirmed':True,'source':'live','resources':[],'quoted_at':snapshot['queried_at']})
        result=rank({'context':'historical-store-delivery','required':group['required'],'drink_mode':'indifferent'},quotes,datetime.fromisoformat(snapshot['queried_at']))
        out['results'].append({'flavor':group['flavor'],'best':result['best']['id'],'payable_fen':result['best']['payable_fen'],'combo_extra_fen':max(q['payable_fen'] for q in quotes)-result['best']['payable_fen']})
    return out

if __name__=='__main__':print(json.dumps(replay(),ensure_ascii=True,indent=2))
