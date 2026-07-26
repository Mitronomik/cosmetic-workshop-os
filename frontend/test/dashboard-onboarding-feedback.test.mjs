import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { bindActionControls, DashboardOnboardingFeedbackLifecycle, onboardingFailureMessage, onboardingSuccessMessage, selectOnboardingFocusTarget } from '../dist-tests/dashboard-onboarding-feedback/dashboard-onboarding-feedback.js';
import { DASHBOARD_READ_SOURCE_KEYS, DASHBOARD_READ_TIMEOUT_MS, DashboardReadCoordinator } from '../dist-tests/dashboard-onboarding-feedback/dashboard-read-runtime.js';
import { alertListResponseDtoIsValid, clientsListDtoIsValid, productionBatchListResponseDtoIsValid, purchaseSuggestionListResponseDtoIsValid } from '../dist-tests/dashboard-onboarding-feedback/dashboard-read-validators.js';
const data=(n)=>({orders:Array(n).fill({}),clients:[],alerts:[],purchaseSuggestions:[],productionBatches:[]});
const emptyData=()=>data(0);
const state=(step='welcome')=>({has_started:true,is_completed:false,current_step:step,completed_steps:[],available_steps:['welcome','stock']});
function assertDashboardInvariant(c){ const d=c.state.dashboard; assert.equal(Boolean(d.message&&d.error),false); assert.equal(Boolean(d.message&&d.warning),false); assert.equal(d.status==='loading'&&Boolean(d.message||d.error||d.warning),false); assert.equal(Boolean(d.error&&d.warning),false); }
function assertOnboardingInvariant(c){ const o=c.state.onboarding; assert.equal(Boolean(o.message&&o.error),false); assert.equal(Boolean(o.message&&o.warning),false); assert.equal((o.loadActive||o.mutationActive)&&Boolean(o.message||o.error||o.warning),false); assert.equal(o.status==='unavailable'&&Boolean(o.state),false); }
const deferred=()=>{ let resolve; let reject; const promise=new Promise((yes,no)=>{resolve=yes;reject=no;}); return {promise,resolve,reject}; };
const flush=()=>new Promise((resolve)=>setImmediate(resolve));
function fakeScheduler(){ let next=0; const active=new Map(); return { delays:[], cleared:[], setTimeout(callback,delay){ const id=++next; this.delays.push(delay); active.set(id,callback); return id; }, clearTimeout(id){ this.cleared.push(id); active.delete(id); }, run(id=active.keys().next().value){ const callback=active.get(id); if(callback){ active.delete(id); callback(); } }, activeCount(){ return active.size; } }; }
function responseFor(key,generation,valid=true){ const field={orders:'orders',clients:'clients',alerts:'alerts',purchaseSuggestions:'purchase_suggestions',productionBatches:'production_batches'}[key]; return valid ? {[field]:[{generation,key}]} : {[field]:'invalid'}; }
function dashboardHarness(){
  const scheduler=fakeScheduler();
  const deferredByKey=Object.fromEntries(DASHBOARD_READ_SOURCE_KEYS.map((key)=>[key,[]]));
  const calls=[];
  const sources=Object.fromEntries(DASHBOARD_READ_SOURCE_KEYS.map((key)=>[key,{
    read(signal){ const request=deferred(); deferredByKey[key].push(request); calls.push({key,signal}); return request.promise; },
    validate(response){ const field={orders:'orders',clients:'clients',alerts:'alerts',purchaseSuggestions:'purchase_suggestions',productionBatches:'production_batches'}[key]; return Boolean(response&&Array.isArray(response[field])); },
  }]));
  const coordinator=new DashboardReadCoordinator({
    scheduler,
    sources,
    buildCandidate(responses){ return {orders:responses.orders.orders,clients:responses.clients.clients,alerts:responses.alerts.alerts,purchaseSuggestions:responses.purchaseSuggestions.purchase_suggestions,productionBatches:responses.productionBatches.production_batches}; },
  });
  return {scheduler,deferredByKey,calls,coordinator,outcomes:[]};
}
const validClient=()=>({id:1,full_name:'Анна',phone:'',email:'',address:'',birthday:null,skin_notes:'',allergy_notes:'',preference_notes:'',contraindication_notes:'',notes:'',is_active:true,created_at:'2026-07-26T10:00:00',updated_at:'2026-07-26T10:00:00'});
const validAlert=()=>({id:1,alert_key:'low-stock-1',type:'low_ingredient_stock',severity:'warning',message:'Низкий остаток',related_entity_type:'ingredient',related_entity_id:1,recommended_action:'Пополнить запас',status:'open',created_at:'2026-07-26T10:00:00',updated_at:'2026-07-26T10:00:00',resolved_at:null,dismissed_at:null});
const validPurchaseSuggestion=()=>({id:1,suggestion_key:'buy-1',item_type:'ingredient',item_id:1,item_name_snapshot:'Масло',recommended_quantity:'100',unit:'g',reason:'below_minimum_stock',source_entity_type:'alert',source_entity_id:1,message:'Купить масло',status:'open',notes:'',created_at:'2026-07-26T10:00:00',updated_at:'2026-07-26T10:00:00',resolved_at:null});
const validProductionBatch=()=>({id:1,order_id:1,product_name:'Крем',client_id:1,client_name:'Анна',recipe_version_id:1,client_recipe_id:null,final_batch_value:'50',final_batch_unit:'g',total_cost:'200',sale_price:'800',tax:'48',margin:'552',margin_percent:'69',produced_at:'2026-07-26T10:00:00',ingredient_line_count:3,packaging_line_count:1,notes:''});
function productionResponseFor(key){
  if(key==='orders') return {orders:[]};
  if(key==='clients') return {clients:[validClient()]};
  if(key==='alerts') return {alerts:[validAlert()],limit:100,offset:0};
  if(key==='purchaseSuggestions') return {purchase_suggestions:[validPurchaseSuggestion()],limit:100,offset:0};
  return {production_batches:[validProductionBatch()],limit:50,offset:0};
}
function productionValidationHarness(){
  const scheduler=fakeScheduler();
  const deferredByKey=Object.fromEntries(DASHBOARD_READ_SOURCE_KEYS.map((key)=>[key,[]]));
  const calls=[];
  const validators={
    orders:(response)=>Boolean(response&&typeof response==='object'&&!Array.isArray(response)&&Array.isArray(response.orders)),
    clients:clientsListDtoIsValid,
    alerts:alertListResponseDtoIsValid,
    purchaseSuggestions:purchaseSuggestionListResponseDtoIsValid,
    productionBatches:productionBatchListResponseDtoIsValid,
  };
  let candidateBuildCount=0;
  const sources=Object.fromEntries(DASHBOARD_READ_SOURCE_KEYS.map((key)=>[key,{
    read(signal){ const request=deferred(); deferredByKey[key].push(request); calls.push({key,signal}); return request.promise; },
    validate:validators[key],
  }]));
  const coordinator=new DashboardReadCoordinator({
    scheduler,
    sources,
    buildCandidate(responses){ candidateBuildCount+=1; return {orders:responses.orders.orders,clients:responses.clients.clients,alerts:responses.alerts.alerts,purchaseSuggestions:responses.purchaseSuggestions.purchase_suggestions,productionBatches:responses.productionBatches.production_batches}; },
  });
  return {scheduler,deferredByKey,calls,coordinator,outcomes:[],candidateBuildCount:()=>candidateBuildCount};
}
async function verifyProductionInvalidItemCase({source,response},previousSnapshot){
  const h=productionValidationHarness();
  const lifecycle=new DashboardOnboardingFeedbackLifecycle();
  if(previousSnapshot){
    const loaded=lifecycle.startDashboardLoad('initial');
    lifecycle.finishDashboardSuccess(loaded.requestId,previousSnapshot);
  }
  wireDashboardOperation(h,lifecycle,previousSnapshot?'refresh':'initial');
  await flush();
  assert.equal(h.calls.length,5);
  h.deferredByKey[source][0].resolve(response);
  await flush();
  assert.equal(h.outcomes.length,1);
  assert.equal(h.outcomes[0].kind,'invalid-response');
  assert.equal(h.candidateBuildCount(),0);
  assert.equal(lifecycle.state.dashboard.active,false);
  assert.equal(h.coordinator.activeGeneration(),null);
  assert.equal(h.scheduler.activeCount(),0);
  assert.equal(h.scheduler.cleared.length,1);
  assert.equal(h.calls.every((call)=>call.signal.aborted),true);
  if(previousSnapshot){
    assert.equal(lifecycle.state.dashboard.data,previousSnapshot);
    assert.equal(lifecycle.state.dashboard.hasLoadedSnapshot,true);
  }else{
    assert.equal(lifecycle.state.dashboard.data,null);
    assert.equal(lifecycle.state.dashboard.hasLoadedSnapshot,false);
  }
  for(const key of DASHBOARD_READ_SOURCE_KEYS){
    if(key!==source) h.deferredByKey[key][0].resolve(productionResponseFor(key));
  }
  await flush();
  assert.equal(h.outcomes.length,1);
  assert.equal(h.candidateBuildCount(),0);
  assert.equal(lifecycle.state.dashboard.data,previousSnapshot);
  assert.equal(lifecycle.state.dashboard.active,false);
}
function wireDashboardOperation(h,lifecycle,kind='initial',owns=true){
  const started=lifecycle.startDashboardLoad(kind);
  if(!started.accepted) return started;
  h.coordinator.start(started.requestId,(outcome)=>{
    h.outcomes.push(outcome);
    if(outcome.kind==='success') lifecycle.finishDashboardSuccess(outcome.generation,outcome.data,owns);
    else if(outcome.kind==='timeout') lifecycle.finishDashboardTimeout(outcome.generation,owns);
    else if(outcome.kind==='route-detached'||outcome.kind==='superseded') lifecycle.finishDashboardCancellation(outcome.generation);
    else lifecycle.finishDashboardFailure(outcome.generation,owns);
  });
  return started;
}
function resolveGeneration(h,index,generation,order=DASHBOARD_READ_SOURCE_KEYS){
  for(const key of order) h.deferredByKey[key][index].resolve(responseFor(key,generation));
}

test('dashboard initial success/failure and manual refresh announcements',()=>{ const c=new DashboardOnboardingFeedbackLifecycle(); let r=c.startDashboardLoad('initial'); let f=c.finishDashboardSuccess(r.requestId,data(1)); assert.equal(f.announcement,'none'); assert.equal(c.state.dashboard.hasLoadedSnapshot,true); assertDashboardInvariant(c); r=c.startDashboardLoad('refresh'); f=c.finishDashboardSuccess(r.requestId,data(2)); assert.equal(f.announcement,'polite'); assert.equal(c.state.dashboard.message.includes('Обзор обновлён'),true); assertDashboardInvariant(c); const fresh=new DashboardOnboardingFeedbackLifecycle(); r=fresh.startDashboardLoad('initial'); f=fresh.finishDashboardFailure(r.requestId,true); assert.equal(f.announcement,'assertive'); assert.equal(fresh.state.dashboard.error.includes('Не удалось загрузить'),true); assertDashboardInvariant(fresh); });

test('dashboard refresh failure preserves non-empty and valid empty snapshots',()=>{ for (const snapshot of [data(3), emptyData()]) { const c=new DashboardOnboardingFeedbackLifecycle(); let r=c.startDashboardLoad('initial'); c.finishDashboardSuccess(r.requestId,snapshot); assert.equal(c.state.dashboard.hasLoadedSnapshot,true); r=c.startDashboardLoad('refresh'); const f=c.finishDashboardFailure(r.requestId,true); assert.equal(f.announcement,'assertive'); assert.equal(c.state.dashboard.data.orders.length,snapshot.orders.length); assert.equal(c.state.dashboard.error,''); assert.match(c.state.dashboard.warning,/последние|ранее|устар/); assertDashboardInvariant(c); } });

test('dashboard duplicate refresh and stale callbacks cannot mutate newer request',()=>{ const c=new DashboardOnboardingFeedbackLifecycle(); let a=c.startDashboardLoad('initial'); c.finishDashboardSuccess(a.requestId,data(1)); a=c.startDashboardLoad('refresh'); assert.equal(c.startDashboardLoad('refresh').accepted,false); const oldId=a.requestId; c.finishDashboardSuccess(oldId,data(2)); const b=c.startDashboardLoad('refresh'); assert.equal(c.finishDashboardSuccess(oldId,data(9)).accepted,false); assert.equal(c.finishDashboardFailure(oldId,true).accepted,false); assert.equal(c.state.dashboard.active,true); assert.equal(c.state.dashboard.data.orders.length,2); assert.equal(c.state.dashboard.message,''); assert.equal(c.state.dashboard.warning,''); assert.equal(c.state.dashboard.error,''); c.finishDashboardSuccess(b.requestId,data(4)); assert.equal(c.state.dashboard.data.orders.length,4); assertDashboardInvariant(c); });

test('dashboard new operation clears feedback and lost ownership suppresses transient feedback',()=>{ const c=new DashboardOnboardingFeedbackLifecycle(); let r=c.startDashboardLoad('initial'); c.finishDashboardSuccess(r.requestId,data(1)); r=c.startDashboardLoad('refresh'); c.finishDashboardFailure(r.requestId,true); assert.ok(c.state.dashboard.warning); r=c.startDashboardLoad('refresh'); assert.equal(c.state.dashboard.warning,''); assert.equal(c.state.dashboard.error,''); assert.equal(c.state.dashboard.message,''); let f=c.finishDashboardSuccess(r.requestId,data(5),false); assert.equal(f.announcement,'none'); assert.equal(c.state.dashboard.message,''); r=c.startDashboardLoad('refresh'); f=c.finishDashboardFailure(r.requestId,false); assert.equal(f.announcement,'none'); assert.equal(c.state.dashboard.warning,''); assert.equal(c.state.dashboard.status,'ready'); assertDashboardInvariant(c); });

test('dashboard timeout lifecycle distinguishes initial and refresh presentation',()=>{ const c=new DashboardOnboardingFeedbackLifecycle(); let r=c.startDashboardLoad('initial'); let f=c.finishDashboardTimeout(r.requestId,true); assert.equal(f.announcement,'assertive'); assert.match(c.state.dashboard.error,/слишком долго/); assert.match(c.state.dashboard.error,/не изменялись/); assert.equal(c.state.dashboard.active,false); assert.equal(c.finishDashboardTimeout(r.requestId,true).accepted,false); r=c.startDashboardLoad('initial'); c.finishDashboardSuccess(r.requestId,emptyData()); r=c.startDashboardLoad('refresh'); f=c.finishDashboardTimeout(r.requestId,true); assert.equal(f.announcement,'polite'); assert.match(c.state.dashboard.warning,/устаревшими/); assert.equal(c.state.dashboard.hasLoadedSnapshot,true); assert.equal(c.state.dashboard.data.orders.length,0); assertDashboardInvariant(c); });

test('dashboard cancellation is silent and preserves loaded or unloaded state',()=>{ for(const snapshot of [null,emptyData(),data(2)]){ const c=new DashboardOnboardingFeedbackLifecycle(); if(snapshot){ const first=c.startDashboardLoad('initial'); c.finishDashboardSuccess(first.requestId,snapshot); } const started=c.startDashboardLoad(snapshot?'refresh':'initial'); const f=c.finishDashboardCancellation(started.requestId); assert.equal(f.announcement,'none'); assert.equal(f.focusAllowed,false); assert.equal(c.state.dashboard.active,false); assert.equal(c.state.dashboard.status,snapshot?'ready':'idle'); assert.equal(c.state.dashboard.data,snapshot); assert.equal(c.finishDashboardFailure(started.requestId,true).accepted,false); assertDashboardInvariant(c); } });

test('production timeout policy creates one whole-operation deadline and starts five reads together',async()=>{ const h=dashboardHarness(); const c=new DashboardOnboardingFeedbackLifecycle(); const started=wireDashboardOperation(h,c); assert.equal(started.accepted,true); assert.deepEqual(h.scheduler.delays,[DASHBOARD_READ_TIMEOUT_MS]); assert.equal(DASHBOARD_READ_TIMEOUT_MS,8000); await flush(); assert.equal(h.calls.length,5); assert.deepEqual(h.calls.map((call)=>call.key),DASHBOARD_READ_SOURCE_KEYS); assert.equal(new Set(h.calls.map((call)=>call.signal)).size,1); assert.equal(h.scheduler.activeCount(),1); resolveGeneration(h,0,1); await flush(); assert.equal(h.outcomes.length,1); assert.equal(h.outcomes[0].kind,'success'); assert.equal(h.scheduler.activeCount(),0); assert.equal(h.scheduler.cleared.length,1); });

test('five differently ordered valid responses commit one coherent snapshot',async()=>{ const h=dashboardHarness(); const c=new DashboardOnboardingFeedbackLifecycle(); wireDashboardOperation(h,c); await flush(); const order=['productionBatches','alerts','orders','purchaseSuggestions','clients']; resolveGeneration(h,0,7,order); await flush(); assert.equal(h.outcomes.length,1); assert.equal(c.state.dashboard.hasLoadedSnapshot,true); for(const key of DASHBOARD_READ_SOURCE_KEYS){ const field=key; assert.equal(c.state.dashboard.data[field][0].generation,7); assert.equal(c.state.dashboard.data[field][0].key,key); } assert.equal(c.state.dashboard.active,false); assertDashboardInvariant(c); });

test('one timed-out source discards four completed results and rejects late callbacks',async()=>{ const h=dashboardHarness(); const c=new DashboardOnboardingFeedbackLifecycle(); wireDashboardOperation(h,c); await flush(); for(const key of DASHBOARD_READ_SOURCE_KEYS.slice(0,4)) h.deferredByKey[key][0].resolve(responseFor(key,1)); await flush(); assert.equal(c.state.dashboard.data,null); h.scheduler.run(); assert.equal(h.outcomes.length,1); assert.equal(h.outcomes[0].kind,'timeout'); assert.equal(c.state.dashboard.hasLoadedSnapshot,false); assert.equal(c.state.dashboard.active,false); assert.equal(h.calls.every((call)=>call.signal.aborted),true); h.deferredByKey.productionBatches[0].resolve(responseFor('productionBatches',1)); await flush(); assert.equal(h.outcomes.length,1); assert.equal(c.state.dashboard.data,null); assert.equal(h.calls.length,5); });

test('one ordinary failure discards four completed results and clears operation resources',async()=>{ const h=dashboardHarness(); const c=new DashboardOnboardingFeedbackLifecycle(); wireDashboardOperation(h,c); await flush(); for(const key of DASHBOARD_READ_SOURCE_KEYS.slice(0,4)) h.deferredByKey[key][0].resolve(responseFor(key,1)); h.deferredByKey.productionBatches[0].reject(new Error('network')); await flush(); assert.equal(h.outcomes.length,1); assert.equal(h.outcomes[0].kind,'failure'); assert.equal(c.state.dashboard.data,null); assert.equal(c.state.dashboard.active,false); assert.equal(h.scheduler.activeCount(),0); assert.equal(h.scheduler.cleared.length,1); assert.equal(h.calls.every((call)=>call.signal.aborted),true); });

test('one invalid response discards the complete candidate and clears its timer',async()=>{ const h=dashboardHarness(); const c=new DashboardOnboardingFeedbackLifecycle(); wireDashboardOperation(h,c); await flush(); for(const key of DASHBOARD_READ_SOURCE_KEYS) h.deferredByKey[key][0].resolve(responseFor(key,1,key!=='alerts')); await flush(); assert.equal(h.outcomes.length,1); assert.equal(h.outcomes[0].kind,'invalid-response'); assert.equal(c.state.dashboard.hasLoadedSnapshot,false); assert.equal(c.state.dashboard.data,null); assert.equal(h.scheduler.activeCount(),0); assert.equal(h.scheduler.cleared.length,1); });

const invalidDashboardItemCases=[
  {name:'clients rejects null item',source:'clients',response:{clients:[null]}},
  {name:'clients rejects empty object item',source:'clients',response:{clients:[{}]}},
  {name:'alerts rejects null item',source:'alerts',response:{alerts:[null],limit:100,offset:0}},
  {name:'alerts rejects empty object item',source:'alerts',response:{alerts:[{}],limit:100,offset:0}},
  {name:'purchase suggestions rejects null item',source:'purchaseSuggestions',response:{purchase_suggestions:[null],limit:100,offset:0}},
  {name:'purchase suggestions rejects invalid stable ID',source:'purchaseSuggestions',response:{purchase_suggestions:[{...validPurchaseSuggestion(),id:'wrong'}],limit:100,offset:0}},
  {name:'production batches rejects null item',source:'productionBatches',response:{production_batches:[null],limit:50,offset:0}},
  {name:'production batches rejects invalid required produced_at',source:'productionBatches',response:{production_batches:[{...validProductionBatch(),produced_at:null}],limit:50,offset:0}},
];
for(const invalidCase of invalidDashboardItemCases){
  test(`production Dashboard validator ${invalidCase.name} without committing initial or refresh snapshots`,async()=>{
    await verifyProductionInvalidItemCase(invalidCase,null);
    const previousSnapshot={orders:[{id:91}],clients:[validClient()],alerts:[validAlert()],purchaseSuggestions:[validPurchaseSuggestion()],productionBatches:[validProductionBatch()]};
    await verifyProductionInvalidItemCase(invalidCase,previousSnapshot);
  });
}

test('refresh timeout preserves non-empty and valid empty coherent snapshots',async()=>{ for(const snapshot of [data(3),emptyData()]){ const h=dashboardHarness(); const c=new DashboardOnboardingFeedbackLifecycle(); const initial=c.startDashboardLoad('initial'); c.finishDashboardSuccess(initial.requestId,snapshot); wireDashboardOperation(h,c,'refresh'); await flush(); h.scheduler.run(); assert.equal(c.state.dashboard.data,snapshot); assert.equal(c.state.dashboard.hasLoadedSnapshot,true); assert.match(c.state.dashboard.warning,/устаревшими/); assert.equal(c.state.dashboard.active,false); assert.equal(h.calls.length,5); } });

test('manual retry creates a clean generation and succeeds without automatic retry',async()=>{ const h=dashboardHarness(); const c=new DashboardOnboardingFeedbackLifecycle(); const first=wireDashboardOperation(h,c); await flush(); h.scheduler.run(); assert.equal(h.calls.length,5); await flush(); assert.equal(h.calls.length,5); const second=wireDashboardOperation(h,c); assert.equal(second.requestId,first.requestId+1); await flush(); assert.equal(h.calls.length,10); resolveGeneration(h,1,second.requestId); await flush(); assert.equal(h.outcomes.length,2); assert.equal(h.outcomes[1].kind,'success'); assert.equal(c.state.dashboard.data.orders[0].generation,second.requestId); assert.equal(c.state.dashboard.error,''); });

test('duplicate lifecycle starts and duplicate coordinator starts create no extra work',async()=>{ const h=dashboardHarness(); const c=new DashboardOnboardingFeedbackLifecycle(); const first=wireDashboardOperation(h,c); const duplicateInitial=c.startDashboardLoad('initial'); const duplicateRefresh=c.startDashboardLoad('refresh'); const coordinatorDuplicate=h.coordinator.start(99,()=>{throw new Error('must not run');}); assert.equal(first.accepted,true); assert.equal(duplicateInitial.accepted,false); assert.equal(duplicateRefresh.accepted,false); assert.equal(coordinatorDuplicate.accepted,false); assert.equal(h.scheduler.delays.length,1); await flush(); assert.equal(h.calls.length,5); });

test('timeout and abort rejection race settles busy state exactly once',async()=>{ const h=dashboardHarness(); const c=new DashboardOnboardingFeedbackLifecycle(); wireDashboardOperation(h,c); await flush(); for(const call of h.calls) call.signal.addEventListener('abort',()=>h.deferredByKey[call.key][0].reject(new DOMException('Aborted','AbortError')),{once:true}); h.scheduler.run(); await flush(); assert.equal(h.outcomes.length,1); assert.equal(h.outcomes[0].kind,'timeout'); assert.equal(c.state.dashboard.active,false); assert.equal(h.scheduler.cleared.length,1); });

test('ordinary failure winning the deadline race cannot settle again as timeout',async()=>{ const h=dashboardHarness(); const c=new DashboardOnboardingFeedbackLifecycle(); wireDashboardOperation(h,c); await flush(); h.deferredByKey.orders[0].reject(new Error('offline')); await flush(); assert.equal(h.outcomes.length,1); h.scheduler.run(); await flush(); assert.equal(h.outcomes.length,1); assert.equal(h.outcomes[0].kind,'failure'); assert.equal(c.state.dashboard.active,false); });

test('route detachment aborts silently, clears deadline, and ignores late source results',async()=>{ const h=dashboardHarness(); const c=new DashboardOnboardingFeedbackLifecycle(); const loaded=c.startDashboardLoad('initial'); c.finishDashboardSuccess(loaded.requestId,data(2)); wireDashboardOperation(h,c,'refresh'); await flush(); assert.equal(h.coordinator.cancelActive('route-detached'),true); assert.equal(h.outcomes.length,1); assert.equal(h.outcomes[0].kind,'route-detached'); assert.equal(c.state.dashboard.data.orders.length,2); assert.equal(c.state.dashboard.warning,''); assert.equal(c.state.dashboard.error,''); assert.equal(h.scheduler.activeCount(),0); resolveGeneration(h,0,8); await flush(); assert.equal(h.outcomes.length,1); assert.equal(c.state.dashboard.data.orders.length,2); });

test('superseded generation cannot overwrite a newer successful generation',async()=>{ const h=dashboardHarness(); const c=new DashboardOnboardingFeedbackLifecycle(); wireDashboardOperation(h,c); await flush(); h.coordinator.cancelActive('superseded'); const next=wireDashboardOperation(h,c); await flush(); resolveGeneration(h,1,next.requestId); await flush(); assert.equal(c.state.dashboard.data.orders[0].generation,next.requestId); resolveGeneration(h,0,1); await flush(); assert.equal(h.outcomes.length,2); assert.equal(c.state.dashboard.data.orders[0].generation,next.requestId); assert.equal(c.state.dashboard.warning,''); assert.equal(c.state.dashboard.error,''); });

test('lost presentation ownership suppresses timeout feedback, announcement, and focus permission',()=>{ const c=new DashboardOnboardingFeedbackLifecycle(); const started=c.startDashboardLoad('initial'); const result=c.finishDashboardTimeout(started.requestId,false); assert.equal(result.accepted,true); assert.equal(result.announcement,'none'); assert.equal(result.message,''); assert.equal(result.focusAllowed,false); assert.equal(c.state.dashboard.status,'idle'); assert.equal(c.state.dashboard.error,''); });

test('Dashboard safe-read transport is opt-in GET-only and shared callers stay timeout-free',()=>{
  const source=readFileSync(new URL('../src/main.ts',import.meta.url),'utf8');
  assert.match(source,/function apiGet<T>\(url: string, signal\?: AbortSignal\)/);
  assert.match(source,/fetch\(url, signal \? \{ signal \} : undefined\)/);
  assert.match(source,/function apiSend<T>\(url: string, method: 'POST' \| 'PUT' \| 'PATCH', body\?: unknown\)/);
  assert.doesNotMatch(source,/function apiSend<T>\([^\n]*AbortSignal/);
  for(const name of ['getOrders','getClients','getAlerts','getPurchaseSuggestions','getProductionBatches']) assert.match(source,new RegExp(`function ${name}\\([^\\n]*signal\\?: AbortSignal`));
  assert.match(source,/read: \(signal\) => getOrders\(true, signal\)/);
  assert.match(source,/read: \(signal\) => getClients\(true, signal\)/);
  assert.match(source,/read: \(signal\) => getAlerts\([^\n]+, signal\)/);
  assert.match(source,/read: \(signal\) => getPurchaseSuggestions\([^\n]+, signal\)/);
  assert.match(source,/read: \(signal\) => getProductionBatches\(signal\)/);
  assert.match(source,/getProductionBatches\(\)\.then/);
  assert.match(source,/getClients\(true\), getRecipeTemplates/);
  assert.match(source,/getAlerts\(started\.filters as AlertsState\['filters'\]\)/);
});

test('onboarding initial and manual load lifecycle clears stale feedback and preserves stale state',()=>{ const c=new DashboardOnboardingFeedbackLifecycle(); let r=c.startOnboardingLoad('initial'); let f=c.finishOnboardingLoadSuccess(r.requestId,state('welcome'),true); assert.equal(f.announcement,'none'); assert.equal(c.state.onboarding.status,'ready'); r=c.startOnboardingMutation('start'); c.finishOnboardingMutationFailure(r.requestId,onboardingFailureMessage('start'),true); assert.ok(c.state.onboarding.error); r=c.startOnboardingLoad('refresh'); assert.equal(c.state.onboarding.error,''); assert.equal(c.state.onboarding.message,''); assert.equal(c.state.onboarding.warning,''); f=c.finishOnboardingLoadSuccess(r.requestId,state('stock'),true); assert.equal(f.announcement,'polite'); assert.equal(c.state.onboarding.message,'Список первых шагов обновлён.'); assertOnboardingInvariant(c); r=c.startOnboardingLoad('refresh'); f=c.finishOnboardingLoadFailure(r.requestId,true); assert.equal(f.announcement,'assertive'); assert.equal(c.state.onboarding.status,'ready'); assert.equal(c.state.onboarding.state.current_step,'stock'); assert.match(c.state.onboarding.warning,/последнее успешно/); assertOnboardingInvariant(c); });

test('onboarding initial load failure unavailable only without state and lost ownership suppresses feedback',()=>{ const c=new DashboardOnboardingFeedbackLifecycle(); let r=c.startOnboardingLoad('initial'); let f=c.finishOnboardingLoadFailure(r.requestId,true); assert.equal(f.announcement,'assertive'); assert.equal(c.state.onboarding.status,'unavailable'); assert.equal(c.state.onboarding.state,null); const c2=new DashboardOnboardingFeedbackLifecycle(); r=c2.startOnboardingLoad('initial'); f=c2.finishOnboardingLoadSuccess(r.requestId,state(),false); assert.equal(f.announcement,'none'); assert.equal(c2.state.onboarding.message,''); r=c2.startOnboardingLoad('refresh'); f=c2.finishOnboardingLoadFailure(r.requestId,false); assert.equal(f.announcement,'none'); assert.equal(c2.state.onboarding.status,'ready'); assert.equal(c2.state.onboarding.warning,''); assertOnboardingInvariant(c2); });

test('onboarding duplicate refresh and mutation/refresh conflicts',()=>{ const c=new DashboardOnboardingFeedbackLifecycle(); c.finishOnboardingLoadSuccess(c.startOnboardingLoad('initial').requestId,state()); let r=c.startOnboardingLoad('refresh'); assert.equal(r.accepted,true); assert.equal(c.startOnboardingLoad('refresh').accepted,false); assert.equal(c.startOnboardingMutation('skip').accepted,false); c.finishOnboardingLoadSuccess(r.requestId,state('stock'),true); r=c.startOnboardingMutation('skip'); assert.equal(r.accepted,true); assert.equal(c.startOnboardingLoad('refresh').accepted,false); assert.equal(c.startOnboardingMutation('reset').accepted,false); c.finishOnboardingMutationSuccess(r.requestId,state('stock'),onboardingSuccessMessage('skip'),true); assertOnboardingInvariant(c); });

test('onboarding stale refresh success/failure cannot clear current owner',()=>{ const c=new DashboardOnboardingFeedbackLifecycle(); let r=c.startOnboardingLoad('initial'); c.finishOnboardingLoadSuccess(r.requestId,state('welcome'),true); r=c.startOnboardingLoad('refresh'); c.finishOnboardingLoadSuccess(r.requestId,state('stock'),true); const oldId=r.requestId; const next=c.startOnboardingLoad('refresh'); assert.equal(c.finishOnboardingLoadSuccess(oldId,state('welcome'),true).accepted,false); assert.equal(c.finishOnboardingLoadFailure(oldId,true).accepted,false); assert.equal(c.state.onboarding.loadActive,true); assert.equal(c.state.onboarding.state.current_step,'stock'); c.finishOnboardingLoadSuccess(next.requestId,state('stock'),true); assertOnboardingInvariant(c); });

for (const action of ['start','complete-step','skip','reset']) test(`onboarding ${action} success and failure use authoritative response`,()=>{ const c=new DashboardOnboardingFeedbackLifecycle(); const before=state('welcome'); c.finishOnboardingLoadSuccess(c.startOnboardingLoad('initial').requestId,before); let r=c.startOnboardingMutation(action); let updated=state('stock'); let f=c.finishOnboardingMutationSuccess(r.requestId,updated,onboardingSuccessMessage(action),true); assert.equal(f.announcement,'polite'); assert.equal(c.state.onboarding.state,updated); assert.equal(c.state.onboarding.error,''); r=c.startOnboardingMutation(action); f=c.finishOnboardingMutationFailure(r.requestId,onboardingFailureMessage(action),true); assert.equal(f.announcement,'assertive'); assert.equal(c.state.onboarding.state,updated); assert.equal(c.state.onboarding.message,''); assert.equal(c.state.onboarding.error,onboardingFailureMessage(action)); assertOnboardingInvariant(c); });

test('onboarding stale mutation success and failure cannot overwrite current busy owner',()=>{ const c=new DashboardOnboardingFeedbackLifecycle(); c.finishOnboardingLoadSuccess(c.startOnboardingLoad('initial').requestId,state('welcome')); let a=c.startOnboardingMutation('start'); c.invalidateOnboardingMutation(); let b=c.startOnboardingMutation('skip'); assert.equal(c.finishOnboardingMutationSuccess(a.requestId,state('old'),onboardingSuccessMessage('start'),true).accepted,false); assert.equal(c.finishOnboardingMutationFailure(a.requestId,onboardingFailureMessage('start'),true).accepted,false); assert.equal(c.state.onboarding.mutationActive,true); assert.equal(c.state.onboarding.action,'skip'); assert.equal(c.state.onboarding.state.current_step,'welcome'); assert.equal(c.state.onboarding.message,''); c.finishOnboardingMutationSuccess(b.requestId,state('stock'),onboardingSuccessMessage('skip'),true); assert.equal(c.state.onboarding.state.current_step,'stock'); assertOnboardingInvariant(c); });

test('onboarding lost ownership suppresses announcements and focus',()=>{ const c=new DashboardOnboardingFeedbackLifecycle(); c.finishOnboardingLoadSuccess(c.startOnboardingLoad('initial').requestId,state()); let r=c.startOnboardingMutation('reset'); let f=c.finishOnboardingMutationSuccess(r.requestId,state('stock'),onboardingSuccessMessage('reset'),false); assert.equal(f.announcement,'none'); assert.equal(f.focusAllowed,false); assert.equal(c.state.onboarding.message,''); r=c.startOnboardingMutation('reset'); f=c.finishOnboardingMutationFailure(r.requestId,onboardingFailureMessage('reset'),false); assert.equal(f.announcement,'none'); assert.equal(f.focusAllowed,false); assert.equal(c.state.onboarding.error,''); assertOnboardingInvariant(c); });

test('focus policy chooses real targets without live regions',()=>{ const previous={key:'complete-step',kind:'previous',enabled:true,attached:true}; const disabled={...previous,enabled:false}; const detached={...previous,attached:false}; const heading={key:'onboarding-heading',kind:'heading',enabled:true,attached:true}; const primary={key:'start-onboarding',kind:'primary',enabled:true,attached:true}; const live={key:'announcer',kind:'live-region',enabled:true,attached:true}; assert.equal(selectOnboardingFocusTarget(true,'complete-step',[previous,heading,primary]),'complete-step'); assert.equal(selectOnboardingFocusTarget(true,'complete-step',[disabled,heading,primary]),'onboarding-heading'); assert.equal(selectOnboardingFocusTarget(true,'complete-step',[detached,primary]),'start-onboarding'); assert.equal(selectOnboardingFocusTarget(true,'missing',[heading,primary,live]),'onboarding-heading'); assert.equal(selectOnboardingFocusTarget(true,'missing',[primary,live]),'start-onboarding'); assert.equal(selectOnboardingFocusTarget(false,'complete-step',[previous,heading,primary]),null); assert.equal(selectOnboardingFocusTarget(true,'announcer',[live]),null); });


test('bindActionControls wires every Dashboard reload control exactly once and handles zero matches',()=>{ let calls=0; const controls=[fakeControl(),fakeControl()]; const root={querySelectorAll:(selector)=>selector==='[data-action="reload-dashboard"]'?controls:[]}; assert.equal(bindActionControls(root,'[data-action="reload-dashboard"]',()=>{ calls+=1; }),2); assert.equal(controls[0].listenerCount(),1); assert.equal(controls[1].listenerCount(),1); controls[0].click(); assert.equal(calls,1); controls[1].click(); assert.equal(calls,2); assert.equal(bindActionControls({querySelectorAll:()=>[]},'[data-action="reload-dashboard"]',()=>{ calls+=1; }),0); assert.equal(calls,2); });

test('bindActionControls wires multiple onboarding refresh controls and lifecycle still rejects duplicate refresh',()=>{ let calls=0; const controls=[fakeControl(),fakeControl(),fakeControl()]; const root={querySelectorAll:(selector)=>selector==='[data-action="refresh-onboarding"]'?controls:[]}; assert.equal(bindActionControls(root,'[data-action="refresh-onboarding"]',()=>{ calls+=1; }),3); controls[0].click(); controls[1].click(); controls[2].click(); assert.equal(calls,3); const lifecycle=new DashboardOnboardingFeedbackLifecycle(); lifecycle.finishOnboardingLoadSuccess(lifecycle.startOnboardingLoad('initial').requestId,state()); const first=lifecycle.startOnboardingLoad('refresh'); const duplicate=lifecycle.startOnboardingLoad('refresh'); assert.equal(first.accepted,true); assert.equal(duplicate.accepted,false); });

function fakeControl(){ const listeners=[]; return { addEventListener(type, listener){ assert.equal(type,'click'); listeners.push(listener); }, click(){ listeners.forEach((listener)=>listener()); }, listenerCount(){ return listeners.length; } }; }
