export type LocalArtifactFolderKind = 'backups' | 'exports' | 'reportDocuments' | 'data';

export type LocalArtifactInput = {
  filename?: string | null;
  path?: string | null;
  createdAt?: string | null;
  reason?: string | null;
  sizeBytes?: number | null;
  folderKind: LocalArtifactFolderKind;
};

export type LocalArtifactPresentation = {
  filename: string;
  createdAtLabel: string;
  reasonLabel: string;
  sizeLabel: string;
  localStatusLabel: string;
  folderLabel: string;
  technicalPath: string | null;
};

const FILENAME_FALLBACK = 'Имя файла недоступно';
const REASON_FALLBACK = 'Причина не указана';
const DATE_FALLBACK = 'Дата недоступна';
const SIZE_FALLBACK = 'Размер недоступен';

const folderLabels: Record<LocalArtifactFolderKind, string> = {
  backups: 'Папка резервных копий',
  exports: 'Папка экспорта',
  reportDocuments: 'Папка документов отчётов',
  data: 'Папка данных приложения',
};

export function basenameFromPath(path: string | null | undefined): string {
  const value = textOrEmpty(path);
  if (!value) return '';
  const withoutTrailing = value.replace(/[\\/]+$/, '');
  const parts = withoutTrailing.split(/[\\/]+/);
  return parts[parts.length - 1]?.trim() ?? '';
}

export function artifactFilename(filename: string | null | undefined, path?: string | null): string {
  const authoritative = textOrEmpty(filename);
  if (authoritative) return authoritative;
  return basenameFromPath(path) || FILENAME_FALLBACK;
}

export function artifactReason(reason: string | null | undefined): string {
  return textOrEmpty(reason) || REASON_FALLBACK;
}

export function artifactDate(value: string | null | undefined): string {
  const raw = textOrEmpty(value);
  if (!raw) return DATE_FALLBACK;
  const parseable = raw.includes('T') ? raw : raw.replace(' ', 'T');
  const date = new Date(parseable);
  if (Number.isNaN(date.getTime())) return DATE_FALLBACK;
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' }).format(date);
}

export function artifactSize(bytes: number | null | undefined): string {
  if (bytes == null || !Number.isFinite(bytes) || bytes < 0) return SIZE_FALLBACK;
  if (bytes === 0) return '0 Б';
  const units = ['Б', 'КБ', 'МБ', 'ГБ'];
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${new Intl.NumberFormat('ru-RU', { maximumFractionDigits: value >= 10 || unitIndex === 0 ? 0 : 1 }).format(value)} ${units[unitIndex]}`;
}

export function artifactFolderLabel(kind: LocalArtifactFolderKind): string {
  return folderLabels[kind];
}

export function localArtifactPresentation(input: LocalArtifactInput): LocalArtifactPresentation {
  return {
    filename: artifactFilename(input.filename, input.path),
    createdAtLabel: artifactDate(input.createdAt),
    reasonLabel: artifactReason(input.reason),
    sizeLabel: artifactSize(input.sizeBytes),
    localStatusLabel: 'Сохранено локально',
    folderLabel: artifactFolderLabel(input.folderKind),
    technicalPath: textOrEmpty(input.path) ? input.path ?? null : null,
  };
}

function textOrEmpty(value: string | null | undefined): string {
  return typeof value === 'string' ? value.trim() : '';
}
