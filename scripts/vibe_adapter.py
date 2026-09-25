"""Only reviewed offline checks; do not invoke upstream main or dependency/live checks."""
import importlib.util
import json
from pathlib import Path
import sys
spec=importlib.util.spec_from_file_location('vibe_vendor',Path(__file__).parent/'vendor'/'vibe'/'audit.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
root=Path(sys.argv[1]).resolve()
findings=[];checks=[]
for name in ['check_config','check_platform_flags','check_rate_limit_and_ai','check_authz','check_platform_configs']:
    rows=[]
    try:
        getattr(m,name)(root,rows)
        # Keep heuristic titles and locations, never source-derived details or fixes.
        findings.extend({k:r[k] for k in ['id','severity','title','where']} for r in rows)
        checks.append({'id':'vibe.'+name,'status':'completed'})
    except Exception:
        checks.append({'id':'vibe.'+name,'status':'error','reason':'Static check failed.'})
print(json.dumps({'findings':findings,'checks':checks}))
