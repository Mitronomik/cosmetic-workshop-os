import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

const root = process.argv[2] ?? '.';
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' };

createServer(async (request, response) => {
  const url = new URL(request.url ?? '/', 'http://127.0.0.1:5173');
  const path = normalize(url.pathname === '/' ? '/index.html' : url.pathname);
  try {
    const body = await readFile(join(root, path));
    response.writeHead(200, { 'content-type': types[extname(path)] ?? 'application/octet-stream' });
    response.end(body);
  } catch {
    response.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
    response.end('Страница не найдена');
  }
}).listen(5173, '127.0.0.1', () => console.log('Frontend: http://127.0.0.1:5173'));
