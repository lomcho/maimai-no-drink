"""Full-menu discovery and lookup. No fixed food IDs or inferred prices."""
import json, sys, unicodedata
from pathlib import Path

def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKC', text).casefold() if c.isalnum())

def build_index(menu, details, failures=None):
    meals = menu['meals']; failures = failures or {}
    index = {}
    def add(code, name, parent, kind):
        row = index.setdefault(code, {'code': code, 'names': [], 'parents': [], 'kinds': []})
        for key,value in [('names',name),('parents',parent),('kinds',kind)]:
            if value and value not in row[key]: row[key].append(value)
    for code,m in meals.items(): add(code,m['name'],None,'menu')
    for code,d in details.items():
        add(code,d.get('name'),None,'combo' if d.get('rounds') else 'single')
        for group in d.get('rounds',[]):
            for choice in group.get('choices',[]):
                add(choice['code'],choice['name'],code,'choice')
    pending=sorted(set(meals)-set(details))
    return {'menu_count':len(meals),'detail_count':len(set(meals)&set(details)),
            'discovery_complete':not pending,'unread_codes':pending,
            'failures':failures,'items':list(index.values()),
            'price_search_complete':False}

def lookup(index,query):
    q=normalize(query)
    if not q: raise ValueError('Empty food query')
    exact=[r for r in index['items'] if any(normalize(n)==q for n in r['names'])]
    partial=[r for r in index['items'] if any(q in normalize(n) for n in r['names'])]
    hits=exact or partial
    return {'query':query,'status':'exact' if len(exact)==1 else 'needs_confirmation' if hits else 'not_found_in_returned_menu' if index['discovery_complete'] else 'discovery_incomplete',
            'matches':hits,'note':'Substring matches are suggestions, not authorized substitutions. Absence is limited to this store/channel/time.'}

def scan(context, destination):
    from mcp_readonly import Client
    from datetime import datetime
    client=Client(); client.discover()
    def data(name,args):
        result=client.tool(name,args)['structuredContent']
        if result.get('success') is False or result.get('code',200)!=200: raise ValueError('Official query unsuccessful')
        if 'data' not in result: raise ValueError('Missing official data')
        return result['data']
    menu=data('query-meals',context); details={}; failures={}
    # No category/name exclusion: menu entries may conceal relevant choices.
    for i,code in enumerate(menu['meals'],1):
        try: details[code]=data('query-meal-detail',{**context,'code':code})
        except Exception as exc:
            failures[code]=type(exc).__name__
            # Stop on service/auth errors instead of hammering failed requests.
            break
        if i%20==0: print(f'Details read: {i}/{len(menu["meals"])}',file=sys.stderr,flush=True)
    report={'queried_at':datetime.now().astimezone().isoformat(timespec='seconds'),
            'context':context,'menu':menu,'details':details,'index':build_index(menu,details,failures)}
    Path(destination).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report['index']

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if sys.argv[1]=='scan':
        result=scan(json.load(sys.stdin),sys.argv[2]);print(json.dumps({k:v for k,v in result.items() if k!='items'},ensure_ascii=False))
    elif sys.argv[1]=='find':
        index=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))['index']
        print(json.dumps([lookup(index,q) for q in sys.argv[3:]],ensure_ascii=False,indent=2))
