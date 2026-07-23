import { transitionLocalArtifactRouteOwnership, type LocalArtifactRouteKey } from './local-artifacts-reports-feedback.js';
import type { LocalArtifactRouteRuntime } from './local-artifacts-reports-runtime.js';

export function transitionLocalArtifactsReportsRouteOwnership(runtimes: Partial<Record<LocalArtifactRouteKey, Pick<LocalArtifactRouteRuntime<unknown, unknown, unknown>, 'enter' | 'leave'>>>, previous: LocalArtifactRouteKey | null, next: LocalArtifactRouteKey | null) {
  transitionLocalArtifactRouteOwnership(runtimes as any, previous, next);
}
