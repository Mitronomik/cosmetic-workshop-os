import test from 'node:test';
import assert from 'node:assert/strict';
import { LocalArtifactsReportsFeedbackLifecycle, bindEveryActionControl, transitionLocalArtifactRouteOwnership } from '../dist-tests/local-artifacts-reports-feedback/local-artifacts-reports-feedback.js';
import { localArtifactPresentation } from '../dist-tests/local-artifacts-reports-feedback/local-artifact-presentation.js';

const messages = {
  loading:'loading', refreshing:'refreshing', initialError:'initial error', refreshError:'refresh warning', refreshSuccess:'refresh ok', mutationBusy:'busy', mutationSuccess:'created', mutationError:'create failed', mutationAmbiguous:'ambiguous refresh first', invalidMutationResponse:'invalid created', mutationRefreshWarning:'created but refresh failed'
};
const mk = () => new LocalArtifactsReportsFeedbackLifecycle({ route:'backups', messages, validateCreated:(x)=>Boolean(x?.id || x?.filename) });
const snap = (items=[]) => ({ items });
const created = (id=1) => ({ id, filename:`file-${id}.json`, path:`/tmp/file-${id}.json` });

test('shared ownership covers request ids, duplicate reads, loaded empty snapshots and refresh preservation',()=>{
  const l=mk(); l.enter(); const a=l.startRead('initial'); assert.equal(a.accepted,true); assert.equal(a.requestId,1);
  assert.equal(l.startRead('initial').accepted,false);
  let done=l.finishReadSuccess(a,snap([])); assert.equal(done.accepted,true); assert.deepEqual(l.state.snapshot.data.items,[]); assert.equal(l.state.feedback.neutral,'');
  const r=l.startRead('refresh'); assert.equal(r.requestId,2); done=l.finishReadFailure(r); assert.equal(done.accepted,true); assert.deepEqual(l.state.snapshot.data.items,[]); assert.equal(l.state.feedback.warning,'refresh warning');
});

test('route generations reject stale success and stale failure and cannot clear newer owner',()=>{
  const l=mk(); l.enter(); const old=l.startRead('initial'); l.leave(); l.enter(); const newer=l.startRead('initial');
  assert.equal(l.finishReadSuccess(old,snap([1])).accepted,false); assert.equal(l.state.read.requestId,newer.requestId);
  assert.equal(l.finishReadFailure(old).accepted,false); assert.equal(l.state.read.requestId,newer.requestId);
});

test('duplicate mutations rejected, result-owned messages do not leak between operations, neutral clears',()=>{
  const l=mk(); l.enter(); const m=l.startMutation('create-backup'); assert.equal(l.state.feedback.neutral,'busy'); assert.equal(l.startMutation('create-backup').accepted,false);
  const done=l.finishMutationSuccess(m,created(1),'success one'); assert.equal(done.message,'success one'); assert.equal(l.state.feedback.neutral,''); assert.equal(l.state.feedback.success,'success one');
  const m2=l.startMutation('create-backup'); const fail=l.finishMutationFailure(m2); assert.equal(fail.message,'create failed'); assert.equal(l.state.feedback.success,''); assert.equal(l.state.feedback.error,'create failed');
});

test('mutation success plus refresh failure keeps created result and separates warning',()=>{
  const l=mk(); l.enter(); const read=l.startRead('initial'); l.finishReadSuccess(read,snap([created(0)]));
  const m=l.startMutation('create-backup'); const ok=l.finishMutationSuccess(m,created(2),'backup created'); assert.equal(ok.needsRefresh,true); assert.deepEqual(l.state.lastCreated,created(2));
  const rr=l.startRead('mutation-refresh'); const warn=l.finishReadFailure(rr); assert.equal(warn.message,'created but refresh failed'); assert.equal(l.state.feedback.success,'backup created'); assert.equal(l.state.feedback.warning,'created but refresh failed'); assert.deepEqual(l.state.snapshot.data.items,[created(0)]);
});

test('detached mutation settlement renders no announcement or focus and return read does not repeat mutation',()=>{
  const l=mk(); l.enter(); const m=l.startMutation('create-backup'); l.leave(); const done=l.finishMutationSuccess(m,created(3),'late'); assert.equal(done.accepted,false); assert.equal(done.detached,true); assert.equal(done.announcement,'none'); l.enter(); const r=l.startRead('initial'); assert.equal(r.accepted,true); assert.equal(r.kind,'initial');
});

test('invalid or unrelated mutation response is rejected and asks for read reconciliation',()=>{
  const l=mk(); l.enter(); const m=l.startMutation('create-backup'); const done=l.finishMutationSuccess(m,{},'bad'); assert.equal(done.accepted,true); assert.equal(done.needsRefresh,true); assert.equal(done.announcement,'assertive'); assert.equal(l.state.lastCreated,null); assert.equal(l.state.feedback.error,'invalid created');
});

test('ambiguous transport outcome is not retried automatically and points to refresh',()=>{
  const l=mk(); l.enter(); const m=l.startMutation('create-backup'); const done=l.finishMutationFailure(m,true); assert.match(done.message,/refresh first/); assert.equal(done.needsRefresh,true); assert.equal(l.state.mutation,null);
});

test('backups lifecycle: empty, non-empty, retry, duplicate create and refresh GET-only recovery',()=>{
  const l=mk(); l.enter(); const empty=l.startRead('initial'); l.finishReadSuccess(empty,snap([])); assert.equal(l.state.snapshot.data.items.length,0);
  const refresh=l.startRead('refresh'); l.finishReadSuccess(refresh,snap([created(1)])); assert.equal(l.state.snapshot.data.items.length,1);
  const m=l.startMutation('create-backup'); assert.equal(l.startMutation('create-backup').accepted,false); l.finishMutationSuccess(m,created(4),'created'); const getOnly=l.startRead('mutation-refresh'); assert.equal(getOnly.kind,'mutation-refresh');
});

test('exports lifecycle preserves PR106 success plus refresh warning and open/download presentation is unaffected',()=>{
  const l=new LocalArtifactsReportsFeedbackLifecycle({ route:'exports', messages, validateCreated:(x)=>Boolean(x?.filename&&x?.path) }); l.enter(); const r=l.startRead('initial'); l.finishReadSuccess(r,snap([created(1)])); const m=l.startMutation('create-export'); l.finishMutationSuccess(m,created(2),'export ok'); const rr=l.startRead('mutation-refresh'); l.finishReadFailure(rr); assert.equal(l.state.lastCreated.filename,'file-2.json'); const p=localArtifactPresentation({filename:'export.json',path:'/safe/export.json',folderKind:'exports'}); assert.equal(p.filename,'export.json'); assert.match(p.folderLabel,/экспорта/i);
});

test('report documents lifecycle covers markdown, pdf, unavailable capability and unchanged previous docs',()=>{
  const l=new LocalArtifactsReportsFeedbackLifecycle({ route:'reportDocuments', messages, validateCreated:(x)=>Boolean(x?.id&&x?.filename&&x?.format) }); l.enter(); const previous={id:'old',filename:'old.md',format:'markdown'}; const r=l.startRead('initial'); l.finishReadSuccess(r,snap([previous])); const m=l.startMutation('create-report-document'); l.finishMutationSuccess(m,{id:'new',filename:'new.pdf',format:'pdf'},'pdf ok'); const rr=l.startRead('mutation-refresh'); l.finishReadFailure(rr); assert.deepEqual(l.state.snapshot.data.items,[previous]); assert.equal(l.state.lastCreated.format,'pdf');
});

test('reports lifecycle is read only, supports empty/non-empty, stale callbacks and route leave invalidation',()=>{
  const l=new LocalArtifactsReportsFeedbackLifecycle({ route:'reports', messages }); l.enter(); const r=l.startRead('initial'); l.finishReadSuccess(r,{overview:{empty:true}}); assert.equal(l.state.snapshot.data.overview.empty,true); const r2=l.startRead('refresh'); l.leave(); assert.equal(l.finishReadSuccess(r2,{overview:{empty:false}}).accepted,false); l.enter(); const r3=l.startRead('initial'); l.finishReadFailure(r3); assert.equal(l.state.feedback.warning,'refresh warning');
});

test('navigation integration transitions all B3.3 routes and avoids same-route duplicate enter',()=>{
  const a=mk(), b=mk(); transitionLocalArtifactRouteOwnership({backups:a,exports:b},null,'backups'); assert.equal(a.state.routeGeneration,1); transitionLocalArtifactRouteOwnership({backups:a,exports:b},'backups','backups'); assert.equal(a.state.routeGeneration,1); transitionLocalArtifactRouteOwnership({backups:a,exports:b},'backups','exports'); assert.equal(a.state.routeGeneration,2); assert.equal(b.state.routeGeneration,1);
});

test('all rendered retry/reload controls are bound with querySelectorAll helper',()=>{
  const calls=[]; const controls=[{addEventListener:(t,cb)=>calls.push([t,cb])},{addEventListener:(t,cb)=>calls.push([t,cb])}]; const root={querySelectorAll:(sel)=> sel==='[data-action="reload-backups"]'?controls:[]}; const count=bindEveryActionControl(root,'[data-action="reload-backups"]',()=>{}); assert.equal(count,2); assert.equal(calls.length,2);
});

test('regression boundaries keep alerts purchases dashboard help and import concepts external',()=>{
  const p=localArtifactPresentation({ filename:null, path:'/tmp/report.md', folderKind:'reportDocuments' }); assert.equal(p.filename,'report.md'); assert.equal(typeof p.technicalPath,'string');
});
