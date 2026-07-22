import type { FeedbackTone } from './purchase-suggestions-feedback';
type VisibleFeedbackTone = Exclude<FeedbackTone, 'none'>;

export type PurchaseFeedbackState = {
  neutral: string;
  success: string;
  refreshWarning: string;
  mutationError: string;
};

export type PurchaseFeedbackItem = { tone: VisibleFeedbackTone; message: string };

export function purchaseFeedbackItems(feedback: PurchaseFeedbackState): PurchaseFeedbackItem[] {
  const items: PurchaseFeedbackItem[] = [];
  if (feedback.neutral) items.push({ tone: 'neutral', message: feedback.neutral });
  if (feedback.success) items.push({ tone: 'success', message: feedback.success });
  if (feedback.refreshWarning) items.push({ tone: 'warning', message: feedback.refreshWarning });
  if (feedback.mutationError) items.push({ tone: 'error', message: feedback.mutationError });
  return items;
}
