import { createServer } from 'node:http';
import { request as httpRequest } from 'node:http';
import { request as httpsRequest } from 'node:https';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

const root = process.argv[2] ?? '.';
const frontendHost = '127.0.0.1';
const frontendPort = 5173;
const frontendOrigin = `http://${frontendHost}:${frontendPort}`;
const apiProxyTarget = new URL(process.env.COSMETIC_WORKSHOP_API_PROXY_TARGET ?? 'http://127.0.0.1:8000');
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' };

function proxyApiRequest(request, response, url) {
  const targetUrl = new URL(`${url.pathname}${url.search}`, apiProxyTarget);
  const proxyRequest = (targetUrl.protocol === 'https:' ? httpsRequest : httpRequest)(
    targetUrl,
    {
      method: request.method,
      headers: {
        ...request.headers,
        host: targetUrl.host,
      },
    },
    (proxyResponse) => {
      response.writeHead(proxyResponse.statusCode ?? 502, proxyResponse.headers);
      proxyResponse.pipe(response);
    },
  );

  proxyRequest.on('error', (error) => {
    console.warn(`API proxy error: ${request.method ?? 'GET'} ${url.pathname}${url.search} -> ${targetUrl.href}: ${error.message}`);
    if (!response.headersSent) {
      response.writeHead(502, { 'content-type': 'text/plain; charset=utf-8' });
    }
    response.end(
      `Не удалось подключиться к локальному backend API. Проверьте, что backend запущен и COSMETIC_WORKSHOP_API_PROXY_TARGET указывает на правильный адрес.\n\nЦель proxy: ${apiProxyTarget.origin}`,
    );
  });

  request.pipe(proxyRequest);
}

createServer(async (request, response) => {
  const url = new URL(request.url ?? '/', frontendOrigin);

  if (url.pathname.startsWith('/api/')) {
    proxyApiRequest(request, response, url);
    return;
  }

  const path = normalize(url.pathname === '/' ? '/index.html' : url.pathname);
  try {
    const body = await readFile(join(root, path));
    response.writeHead(200, { 'content-type': types[extname(path)] ?? 'application/octet-stream' });
    response.end(body);
  } catch {
    if (!extname(path)) {
      const body = await readFile(join(root, 'index.html'));
      response.writeHead(200, { 'content-type': types['.html'] });
      response.end(body);
      return;
    }
    response.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
    response.end('Страница не найдена');
  }
}).listen(frontendPort, frontendHost, () => {
  console.log(`Frontend: ${frontendOrigin}`);
  console.log(`API proxy target: ${apiProxyTarget.origin}`);
});
