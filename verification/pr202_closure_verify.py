from pathlib import Path
import json, os, subprocess

E=Path(os.environ['RUNNER_TEMP'])/'pr202-final-closure-evidence'; E.mkdir(parents=True,exist_ok=True)
BASE=os.environ['EXPECTED_BASE']; HEAD=os.environ['EXPECTED_HEAD']; PR=os.environ['PR_BRANCH']
def out(*a): return subprocess.check_output(a,text=True).strip()
def check(): return subprocess.run(['python3','scripts/check_documentation_lifecycle.py'],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT).returncode
def must_fail(label):
    if check()==0: raise AssertionError(f'negative probe not caught: {label}')
checks={}
try:
    subprocess.run(['git','fetch','origin','main',PR],check=True)
    assert out('git','rev-parse','HEAD')==HEAD and out('git','rev-parse','origin/main')==BASE and out('git','rev-parse',f'origin/{PR}')==HEAD
    assert out('git','status','--porcelain')==''; subprocess.run(['git','diff','--check'],check=True); checks['exact_head']='success'
    files=set(filter(None,out('git','diff','--name-only',f'{BASE}...{HEAD}').splitlines())); assert len(files)==26
    assert not any(p.startswith(('backend/','launcher/','frontend/','macos_package/','migrations/')) for p in files); checks['scope']='success'
    subprocess.run(['python3','-m','py_compile','scripts/check_documentation_lifecycle.py'],check=True); assert check()==0; checks['lifecycle']='success'
    m=json.loads(Path('docs/history/d4-d-pre-closure/manifest.json').read_text(encoding='utf-8'))
    assert m['source_commit']==BASE and m['d4d_final_verification_run']=='31751386881' and m['artifact_id']=='9201217317'
    assert m['artifact_digest']=='sha256:0dc707f8823eb69934a5bc3b3b6824557533bafa3e1e86a7f13fc29c19a1af7d'; checks['snapshot']='success'
    focus=Path('state/current-focus.md'); good=focus.read_text(encoding='utf-8')
    for old,new,label in [
      ('D4 — Update safety — DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED','D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C DONE; D4-D AUTHORIZED NEXT','D4 reopen'),
      ('D4-D — Exact-package update verification and D4 lifecycle closure — DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED','D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED','D4-D revert'),
      ('D5 — Remote install checklist — NOT AUTHORIZED BY CR-013','D5 — Remote install checklist — AUTHORIZED','D5 authorization'),
      ('Product release readiness — NOT CLAIMED','Product release readiness — READY','release readiness'),
      ('Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED','Restore — IN PROGRESS','Restore reopen')]:
        assert old in good; focus.write_text(good.replace(old,new,1),encoding='utf-8'); must_fail(label); focus.write_text(good,encoding='utf-8')
    h=Path('docs/history/d4-d-pre-closure/README.md'); raw=h.read_bytes(); h.write_bytes(raw+b'\nprobe\n'); must_fail('history mutation'); h.write_bytes(raw)
    rt=Path('backend/app/services/update_safety.py'); raw=rt.read_text(encoding='utf-8'); assert 'error.committed' in raw; rt.write_text(raw.replace('error.committed','error.was_committed',1),encoding='utf-8'); must_fail('D4-C runtime seam'); rt.write_text(raw,encoding='utf-8')
    fe=Path('frontend/src/settings-update-status.ts'); raw=fe.read_text(encoding='utf-8'); assert "fetch('/api/settings/status')" in raw; fe.write_text(raw.replace("fetch('/api/settings/status')","fetch('/api/settings/status-broken')",1),encoding='utf-8'); must_fail('D4-C frontend seam'); fe.write_text(raw,encoding='utf-8')
    checks['negative_probes']='success'
    assert check()==0; subprocess.run(['git','diff','--check'],check=True); assert out('git','status','--porcelain')=='' and out('git','rev-parse','HEAD')==HEAD; checks['postflight']='success'; status='passed'
except Exception as exc:
    checks['error']=repr(exc); status='failed'
(E/'results.json').write_text(json.dumps({'pr':202,'base':BASE,'head':HEAD,'status':status,'checks':checks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report=f"# PR #202 final D4 closure verification\n\nExact head: `{HEAD}`\nResult: **{status}**\n\n"+'\n'.join(f'- {k}: {v}' for k,v in checks.items())+'\n\n'+('PASS — D4 FINAL LIFECYCLE CLOSURE VERIFIED' if status=='passed' else 'FAIL — DO NOT MERGE')+'\n'
(E/'PR202_CLOSURE_REPORT.md').write_text(report,encoding='utf-8'); print(report); raise SystemExit(0 if status=='passed' else 1)
