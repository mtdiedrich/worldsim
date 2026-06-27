from worldsim.engine import new_run, step
r = new_run(run_seed=42, n_ticks=2)
step(r)
step(r)
evts = r['world']['event_log']
print(f"Ticks: {r['tick']}, Events: {len(evts)}")
for e in evts[:8]:
    narrative = e.get('narrative') or e['description']
    print(f"  [{e['type']}] {narrative}")
print()
for cid, c in r['world']['cultures'].items():
    print(f"  {c['name']}: pop={c['population']}, food={c['resources']['food']}")
