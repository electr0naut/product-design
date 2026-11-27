import json
rows=[json.loads(l) for l in open('results.jsonl')]
# the reviewer's judgement of what was true: landing reviews, and findings proven by a failing test
REAL={('FXL-1','review-2.json','F1'),('FXL-4','review.json','F1'),('FXL-7','review.json','F2'),('FXL-7','review.json','F4'),('FXL-8','review.json','F1'),('FXL-9','review.json','F1'),('FXL-9','review.json','F2'),('FXL-15','review.json','F3')}|{('FXL-1B','review-3.json',f'F{n}') for n in range(1,5)}
WRONG={('FXL-16','review.json',f'F{n}') for n in range(1,6)}|{('FXL-3B','review.json','F1'),('FXL-9','review.json','F3'),('FXL-9','review.json','F4')}
K=lambda r:(r['key'],r['review'],r['id'])
r1={m:{K(r):r for r in rows if r['model']==m and r['round']==1} for m in ('claude-n/a','qwen4-max','qwen3.7-plus')}
base=r1['qwen4-max']
print('judged real',len(REAL),'| judged wrong',len(WRONG),'| not judged',len(base)-len(REAL)-len(WRONG), '| all keys known', REAL|WRONG <= set(base))
def tally(get, keys):
    out={}
    for k in keys: out[str(get(k))]=out.get(str(get(k)),0)+1
    return out
for name,get in [('Claude (recorded)',lambda k:base[k]['claude']),('qwen4-max',lambda k:r1['qwen4-max'][k]['verdict']),('qwen3.7-plus',lambda k:r1['qwen3.7-plus'][k]['verdict'])]:
    print(f'{name:18} on real: {tally(get,sorted(REAL))}   on wrong: {tally(get,sorted(WRONG))}')
for m in ('qwen4-max','qwen3.7-plus'):
    print('==',m)
    for rnd in (1,2):
        rr=[r for r in rows if r['model']==m and r['round']==rnd]
        hc=[r for r in rr if r['severity'] in ('high','critical')]
        print(f" round {rnd}: Claude blocked, model refuted (would let through):", [K(r) for r in rr if r['blocked'] and r['verdict']=='refuted'])
        print(f"          Claude blocked, model not 'stands':", [(r['key'],r['id'],r['verdict']) for r in rr if r['blocked'] and r['verdict']!='stands'])
        print(f"          high/critical Claude refuted, model did not (goes on to a proof):", [(r['key'],r['id'],r['severity'],r['verdict']) for r in hc if r['claude']=='refuted' and r['verdict']!='refuted'])
        print(f"          medium differences (no effect on the gate):", [(r['key'],r['id'],r['claude'],r['verdict']) for r in rr if r['severity']=='medium' and r['claude']!=r['verdict']])
    calls=[c for r in rows if r['model']==m for c in r['calls']]
    print(' replies rejected:', sum(1 for c in calls if c['why']), 'of', len(calls), '| findings with no verdict after the re-ask:', sum(1 for r in rows if r['model']==m and not r['verdict']))
