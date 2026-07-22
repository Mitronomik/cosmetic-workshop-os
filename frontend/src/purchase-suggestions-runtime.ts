import {
  PurchaseSuggestionFilters,
  PurchaseSuggestionLike,
  PurchaseSuggestionsFeedbackLifecycle,
  GenerationResult,
  ReadKind,
} from "./purchase-suggestions-feedback";
export type PurchaseSuggestionRuntimeDeps<T extends PurchaseSuggestionLike> = {
  read: (filters: PurchaseSuggestionFilters) => Promise<T[]>;
  regenerate: () => Promise<GenerationResult>;
  create: (payload: any) => Promise<T>;
  update: (id: number, payload: any) => Promise<T>;
  markPurchased: (id: number) => Promise<T>;
  dismiss: (id: number) => Promise<T>;
  ownsRoute: () => boolean;
  render: () => void;
  announce: (text: string, kind: "polite" | "assertive") => void;
  focus: (key: string | null) => void;
  onValidCreate?: () => void;
  onValidUpdate?: () => void;
};
export function createPurchaseSuggestionsRuntime<
  T extends PurchaseSuggestionLike,
>(
  lifecycle: PurchaseSuggestionsFeedbackLifecycle<T>,
  deps: PurchaseSuggestionRuntimeDeps<T>,
) {
  function present(r: any) {
    if (!r.present || !deps.ownsRoute()) return;
    deps.render();
    if (r.message && r.announcement !== "none")
      deps.announce(r.message, r.announcement);
    deps.focus(r.focusKey);
  }
  function read(kind: ReadKind, filters: PurchaseSuggestionFilters) {
    const s = lifecycle.startRead(kind, filters);
    if (!s.accepted) return s;
    if (deps.ownsRoute()) deps.render();
    deps
      .read(s.filters)
      .then((items) =>
        present(
          lifecycle.finishReadSuccess(
            s.requestId,
            s.routeGeneration,
            s.filters,
            items,
          ),
        ),
      )
      .catch(() =>
        present(
          lifecycle.finishReadFailure(
            s.requestId,
            s.routeGeneration,
            s.filters,
          ),
        ),
      );
    return s;
  }
  function reconcile() {
    if (!deps.ownsRoute()) return { accepted: false };
    const s = lifecycle.startReconciliationRead(lifecycle.displayedFilters());
    if (!s.accepted) return s;
    deps.render();
    deps
      .read(s.filters)
      .then((items) =>
        present(
          lifecycle.finishReadSuccess(
            s.requestId,
            s.routeGeneration,
            s.filters,
            items,
          ),
        ),
      )
      .catch(() =>
        present(
          lifecycle.finishReadFailure(
            s.requestId,
            s.routeGeneration,
            s.filters,
          ),
        ),
      );
    return s;
  }
  function afterDetached(d: any) {
    if (d.settledDetached && deps.ownsRoute()) reconcile();
  }
  function mutation(kind: any, promise: Promise<T>, owner: any) {
    promise
      .then((dto) => {
        const r = lifecycle.applyResponse(
          owner.requestId,
          owner.routeGeneration,
          kind,
          owner.owner.suggestionId,
          dto,
        );
        if (!r.accepted) {
          afterDetached(
            lifecycle.settleDetachedResponse(
              owner.requestId,
              kind,
              owner.owner.suggestionId,
              dto,
            ),
          );
          return;
        }
        if (r.valid && kind === "create-manual") deps.onValidCreate?.();
        if (r.valid && kind === "update") deps.onValidUpdate?.();
        present(r);
      })
      .catch(() => {
        const r = lifecycle.finishMutationFailure(
          owner.requestId,
          owner.routeGeneration,
          kind,
          owner.owner.suggestionId,
        );
        if (!r.accepted) {
          afterDetached(
            lifecycle.settleDetachedFailure(
              owner.requestId,
              kind,
              owner.owner.suggestionId,
            ),
          );
          return;
        }
        present(r);
      });
  }
  return {
    read,
    reconcile,
    enter() {
      lifecycle.enterRoute();
      if (lifecycle.state.detachedMutation) {
        deps.render();
        return;
      }
      if (lifecycle.hasPendingReconciliation()) {
        reconcile();
        return;
      }
      if (!lifecycle.state.snapshot)
        read("initial", lifecycle.displayedFilters());
      else deps.render();
    },
    leave() {
      lifecycle.leaveRoute();
    },
    regenerate() {
      const s = lifecycle.startMutation("regenerate");
      if (!s.accepted) return s;
      if (deps.ownsRoute()) deps.render();
      deps
        .regenerate()
        .then((result) => {
          const r = lifecycle.finishRegenerationSuccess(
            s.requestId,
            s.routeGeneration,
            result,
          );
          if (!r.accepted) {
            afterDetached(
              lifecycle.settleDetachedRegenerationSuccess(s.requestId, result),
            );
            return;
          }
          present(r);
          if (!deps.ownsRoute()) {
            lifecycle.state.needsReconciliation = true;
            return;
          }
          const g = lifecycle.startRead(
            "regeneration-refresh",
            lifecycle.displayedFilters(),
            s.routeGeneration,
          );
          if (!g.accepted) {
            lifecycle.state.needsReconciliation = true;
            return;
          }
          deps
            .read(g.filters)
            .then((items) =>
              present(
                lifecycle.finishReadSuccess(
                  g.requestId,
                  g.routeGeneration,
                  g.filters,
                  items,
                ),
              ),
            )
            .catch(() =>
              present(
                lifecycle.finishReadFailure(
                  g.requestId,
                  g.routeGeneration,
                  g.filters,
                ),
              ),
            );
        })
        .catch(() => {
          const r = lifecycle.finishMutationFailure(
            s.requestId,
            s.routeGeneration,
            "regenerate",
            null,
          );
          if (!r.accepted)
            afterDetached(
              lifecycle.settleDetachedFailure(s.requestId, "regenerate", null),
            );
          else present(r);
        });
      return s;
    },
    create(payload: any) {
      const s = lifecycle.startMutation("create-manual", undefined, null, {
        expectedItemType: payload.item_type,
        expectedItemId: payload.item_id,
        previousFocusKey: "manual-purchase-form-heading",
      });
      if (s.accepted) {
        if (deps.ownsRoute()) deps.render();
        mutation("create-manual", deps.create(payload), s);
      }
      return s;
    },
    update(id: number, payload: any) {
      const s = lifecycle.startMutation("update", undefined, id, {
        previousFocusKey: `purchase-suggestion-${id}-edit`,
      });
      if (s.accepted) {
        if (deps.ownsRoute()) deps.render();
        mutation("update", deps.update(id, payload), s);
      }
      return s;
    },
    markPurchased(id: number) {
      const s = lifecycle.startMutation("mark-purchased", undefined, id, {
        previousFocusKey: `purchase-suggestion-${id}-mark`,
      });
      if (s.accepted) {
        if (deps.ownsRoute()) deps.render();
        mutation("mark-purchased", deps.markPurchased(id), s);
      }
      return s;
    },
    dismiss(id: number) {
      const s = lifecycle.startMutation("dismiss", undefined, id, {
        previousFocusKey: `purchase-suggestion-${id}-dismiss`,
      });
      if (s.accepted) {
        if (deps.ownsRoute()) deps.render();
        mutation("dismiss", deps.dismiss(id), s);
      }
      return s;
    },
  };
}
