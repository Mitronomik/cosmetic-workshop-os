import { copyFile, cp, mkdir } from 'node:fs/promises';

await mkdir('dist/assets', { recursive: true });
await cp('public', 'dist', { recursive: true });
await copyFile('index.html', 'dist/index.html');
await copyFile('src/styles.css', 'dist/assets/styles.css');
