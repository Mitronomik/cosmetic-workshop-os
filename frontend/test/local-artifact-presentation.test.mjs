import test from 'node:test';
import assert from 'node:assert/strict';
import { artifactDate, artifactFilename, artifactFolderLabel, artifactReason, artifactSize, basenameFromPath, localArtifactPresentation } from '../dist-tests/local-artifact-presentation/local-artifact-presentation.js';

test('authoritative filename is preferred over path basename', () => {
  assert.equal(artifactFilename('backup.json', '/tmp/other.json'), 'backup.json');
});

test('basename fallback supports POSIX paths', () => {
  assert.equal(basenameFromPath('/Users/user/Documents/file.json'), 'file.json');
  assert.equal(artifactFilename('', '/Users/user/Documents/export.json'), 'export.json');
});

test('basename fallback supports Windows paths', () => {
  assert.equal(basenameFromPath('C:\\Users\\user\\Documents\\backup.json'), 'backup.json');
  assert.equal(artifactFilename(null, 'C:\\data\\report.md'), 'report.md');
});

test('empty filename and path use safe fallback', () => {
  assert.equal(artifactFilename('', ''), 'Имя файла недоступно');
});

test('reason normalization trims custom text', () => {
  assert.equal(artifactReason('  Перед проверкой  '), 'Перед проверкой');
});

test('absent reason presentation is explicit', () => {
  assert.equal(artifactReason(null), 'Причина не указана');
});

test('date-unavailable presentation is honest', () => {
  assert.equal(artifactDate(null), 'Дата недоступна');
  assert.equal(artifactDate('not-a-date'), 'Дата недоступна');
});

test('SQLite-style timestamp with a space is parsed as available date', () => {
  const label = artifactDate('2026-07-20 12:34:56');
  assert.notEqual(label, 'Дата недоступна');
  assert.equal(typeof label, 'string');
  assert.ok(label.length > 0);
});

test('size-unavailable presentation is honest', () => {
  assert.equal(artifactSize(undefined), 'Размер недоступен');
  assert.equal(artifactSize(-1), 'Размер недоступен');
});

test('human-readable folder labels are stable', () => {
  assert.equal(artifactFolderLabel('backups'), 'Папка резервных копий');
  assert.equal(artifactFolderLabel('exports'), 'Папка экспорта');
  assert.equal(artifactFolderLabel('reportDocuments'), 'Папка документов отчётов');
  assert.equal(artifactFolderLabel('data'), 'Папка данных приложения');
});

test('technical path remains unchanged when displayed', () => {
  const path = '/tmp/cwo/backups/backup.json';
  const presentation = localArtifactPresentation({ path, folderKind: 'backups' });
  assert.equal(presentation.technicalPath, path);
});

test('technical path preserves meaningful leading and trailing whitespace byte-for-byte', () => {
  const path = '  /tmp/cwo/backups/backup with spaces.json  ';
  const presentation = localArtifactPresentation({ path, folderKind: 'backups' });
  assert.equal(presentation.technicalPath, path);
});

test('empty or whitespace-only technical path becomes null', () => {
  assert.equal(localArtifactPresentation({ path: '', folderKind: 'exports' }).technicalPath, null);
  assert.equal(localArtifactPresentation({ path: '   ', folderKind: 'exports' }).technicalPath, null);
});

test('basename fallback uses normalized path text without changing technical path', () => {
  const path = '  /tmp/cwo/exports/export.json  ';
  const presentation = localArtifactPresentation({ path, folderKind: 'exports' });
  assert.equal(presentation.filename, 'export.json');
  assert.equal(presentation.technicalPath, path);
});

test('escaping remains responsibility of rendering boundary', () => {
  const value = '<script>alert(1)</script>.json';
  assert.equal(artifactFilename(value, null), value);
});
