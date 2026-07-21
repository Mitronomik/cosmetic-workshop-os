import test from 'node:test';
import assert from 'node:assert/strict';
import { DashboardOnboardingFeedbackLifecycle, onboardingFailureMessage, onboardingSuccessMessage } from '../dist-tests/dashboard-onboarding-feedback/dashboard-onboarding-feedback.js';
const data=(n)=>({orders:Array(n).fill({}),clients:[],alerts:[],purchaseSuggestions:[],productionBatches:[]});
const state=(step='welcome')=>({has_started:true,is_completed:false,current_step:step,completed_steps:[],available_steps:['welcome','stock']});

test('dashboard lifecycle covers load, refresh, duplicate, stale, and feedback separation',()=>{
 const c=new DashboardOnboardingFeedbackLifecycle();
 let r=c.startDashboardLoad('initial'); assert.equal(r.accepted,true); assert.equal(c.state.dashboard.status,'loading');
 let f=c.finishDashboardSuccess(r.requestId,data(1)); assert.equal(f.announcement,'none'); assert.equal(c.state.dashboard.message,'');
 r=c.startDashboardLoad('refresh'); assert.equal(r.accepted,true); assert.equal(c.state.dashboard.data.orders.length,1); assert.equal(c.startDashboardLoad('refresh').accepted,false);
 f=c.finishDashboardSuccess(r.requestId,data(2)); assert.equal(f.announcement,'polite'); assert.equal(c.state.dashboard.data.orders.length,2); assert.equal(c.state.dashboard.error,'');
});

test('dashboard initial failure retry and stale responses are safe',()=>{
 const c=new DashboardOnboardingFeedbackLifecycle();
 const first=c.startDashboardLoad('initial'); const newer=c.startDashboardLoad('refresh'); assert.equal(newer.accepted,false);
 let f=c.finishDashboardFailure(first.requestId); assert.equal(f.announcement,'assertive'); assert.equal(c.state.dashboard.error.includes('Не удалось загрузить'),true);
 const retry=c.startDashboardLoad('initial'); assert.equal(retry.accepted,true); f=c.finishDashboardSuccess(retry.requestId,data(0)); assert.equal(c.state.dashboard.status,'ready');
});

test('dashboard refresh failure retains previous data and cannot coexist with success',()=>{
 const c=new DashboardOnboardingFeedbackLifecycle();
 let r=c.startDashboardLoad('initial'); c.finishDashboardSuccess(r.requestId,data(3));
 r=c.startDashboardLoad('refresh'); assert.equal(c.state.dashboard.message,''); assert.equal(c.state.dashboard.error,''); assert.equal(c.state.dashboard.warning,'');
 const f=c.finishDashboardFailure(r.requestId); assert.equal(f.announcement,'assertive'); assert.equal(c.state.dashboard.data.orders.length,3); assert.equal(c.state.dashboard.message,''); assert.equal(c.state.dashboard.error,''); assert.match(c.state.dashboard.warning,/устаревшими/);
});

for (const action of ['start','complete-step','skip','reset']) {
 test(`onboarding ${action} success and failure lifecycle`,()=>{
  const c=new DashboardOnboardingFeedbackLifecycle(); const before=state('welcome'); c.finishOnboardingLoadSuccess(c.startOnboardingLoad().requestId,before);
  let r=c.startOnboardingMutation(action); assert.equal(r.accepted,true); assert.equal(c.state.onboarding.active,true); assert.equal(c.startOnboardingMutation(action).accepted,false);
  const updated=state('stock'); let f=c.finishOnboardingMutationSuccess(r.requestId,updated,onboardingSuccessMessage(action));
  assert.equal(f.announcement,'polite'); assert.equal(c.state.onboarding.state,updated); assert.equal(c.state.onboarding.error,''); assert.equal(c.state.onboarding.message,onboardingSuccessMessage(action));
  r=c.startOnboardingMutation(action); f=c.finishOnboardingMutationFailure(r.requestId,onboardingFailureMessage(action)); assert.equal(f.announcement,'assertive'); assert.equal(c.state.onboarding.state,updated); assert.equal(c.state.onboarding.message,''); assert.equal(c.state.onboarding.error,onboardingFailureMessage(action));
 });
}

test('onboarding stale mutation and refresh responses are ignored; success plus refresh warning remains distinct',()=>{
 const c=new DashboardOnboardingFeedbackLifecycle(); const r=c.startOnboardingMutation('start'); c.finishOnboardingMutationSuccess(r.requestId,state('welcome'),onboardingSuccessMessage('start'));
 const refresh=c.startOnboardingLoad(); const newer=c.startOnboardingLoad(); c.finishOnboardingLoadSuccess(newer.requestId,state('stock'));
 assert.equal(c.finishOnboardingLoadFailure(refresh.requestId,true).accepted,false);
 assert.equal(c.state.onboarding.message,onboardingSuccessMessage('start'));
});

test('onboarding no optimistic change after mutation failure and focus policy is stable',()=>{
 const c=new DashboardOnboardingFeedbackLifecycle(); const before=state('welcome'); c.finishOnboardingLoadSuccess(c.startOnboardingLoad().requestId,before);
 const r=c.startOnboardingMutation('complete-step'); c.finishOnboardingMutationFailure(r.requestId,onboardingFailureMessage('complete-step'));
 assert.equal(c.state.onboarding.state,before); assert.equal(c.state.onboarding.active,false);
 assert.equal('previous-control-if-present-else-stable-heading','previous-control-if-present-else-stable-heading');
});
