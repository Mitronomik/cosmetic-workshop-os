export const PURCHASE_SUGGESTIONS_SECTION = "Закупки";

export type PurchaseRouteRuntime = {
  enter: () => unknown;
  leave: () => unknown;
};

export function transitionPurchaseSuggestionsRouteOwnership({
  previousSection,
  nextSection,
  runtime,
}: {
  previousSection: string | null | undefined;
  nextSection: string | null | undefined;
  runtime: PurchaseRouteRuntime;
}) {
  const wasPurchases = previousSection === PURCHASE_SUGGESTIONS_SECTION;
  const isPurchases = nextSection === PURCHASE_SUGGESTIONS_SECTION;
  if (!wasPurchases && isPurchases) {
    runtime.enter();
    return "enter" as const;
  }
  if (wasPurchases && !isPurchases) {
    runtime.leave();
    return "leave" as const;
  }
  return "none" as const;
}


export type PurchaseNavigationCoordinatorDeps = {
  runtime: PurchaseRouteRuntime;
  referenceController: { leaveRoute: () => unknown };
};

export function createPurchaseSuggestionsNavigationCoordinator({ runtime, referenceController }: PurchaseNavigationCoordinatorDeps) {
  return {
    transition(previousSection: string | null | undefined, nextSection: string | null | undefined) {
      const action = transitionPurchaseSuggestionsRouteOwnership({ previousSection, nextSection, runtime });
      if (action === 'leave') referenceController.leaveRoute();
      return action;
    },
  };
}
