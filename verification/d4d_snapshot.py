import json, os, shutil, subprocess
from pathlib import Path

source=os.environ['D4D_VERIFIED_HEAD']; snap=Path('docs/history/d4-d-pre-closure')
files={'README.md':'README.md','docs/current-lifecycle.md':'current-lifecycle.md','docs/implementation-plan.md':'implementation-plan.md','docs/packaging.md':'packaging.md','docs/deployment.md':'deployment.md','docs/update-guide.md':'update-guide.md','state/current-focus.md':'current-focus.md','state/progress.md':'progress.md','state/handoff.md':'handoff.md','state/change-requests.md':'change-requests.md','scripts/check_documentation_lifecycle.py':'check_documentation_lifecycle.py','docs/history/README.md':'history-README.md'}
if snap.exists(): raise SystemExit('snapshot exists')
snap.mkdir(parents=True)
blobs={}
for src,dst in files.items():
    shutil.copyfile(src,snap/dst); blobs[dst]=subprocess.check_output(['git','hash-object',src],text=True).strip()
manifest={'source_commit':source,'d4d_final_verification_run':os.environ['D4D_RUN'],'artifact_id':os.environ['D4D_ARTIFACT'],'artifact_digest':os.environ['D4D_DIGEST'],'files':blobs}
(snap/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(snap/'ABOUT.md').write_text(f"# D4-D pre-closure snapshot\n\nExact active lifecycle/state/checker surfaces from `{source}` before final D4 closure.\n\nD4-D run: `{os.environ['D4D_RUN']}`; artifact: `{os.environ['D4D_ARTIFACT']}`; digest: `{os.environ['D4D_DIGEST']}`. Final report: `PASS — FULL AUTOMATED SMOKE PASSED`.\n\nEvery copied file is protected by exact Git blob identity in `manifest.json`.\n",encoding='utf-8')
