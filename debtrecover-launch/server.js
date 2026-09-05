const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = Number(process.env.PORT || 3000);
const ROOT = __dirname;
const indexHtml = fs.readFileSync(path.join(ROOT, 'index.html'));
const appJs = fs.readFileSync(path.join(ROOT, 'app.js'));
const health = Buffer.from(JSON.stringify({status:'ok', mode:'synthetic', version:'0.4.5'}), 'utf8');
const notFound = Buffer.from('Not found\n', 'utf8');
const methodNotAllowed = Buffer.from('Method not allowed\n', 'utf8');

const securityHeaders = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'no-referrer',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=()',
  'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
  'Cache-Control': 'no-store',
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Cross-Origin-Resource-Policy': 'same-origin',
  'X-DebtRecover-Mode': 'synthetic-only',
  'X-DebtRecover-Runtime': 'canonical-files-v2'
};

function send(req, res, status, body, contentType, extra = {}) {
  res.writeHead(status, {
    ...securityHeaders,
    ...extra,
    'Content-Type': contentType,
    'Content-Length': body.length
  });
  if (req.method === 'HEAD') return res.end();
  res.end(body);
}

const server = http.createServer((req, res) => {
  if (!['GET', 'HEAD'].includes(req.method)) {
    return send(req, res, 405, methodNotAllowed, 'text/plain; charset=utf-8', {'Allow': 'GET, HEAD'});
  }
  const url = new URL(req.url, 'http://localhost');
  if (url.pathname === '/health') return send(req, res, 200, health, 'application/json; charset=utf-8');
  if (url.pathname === '/' || url.pathname === '/index.html') return send(req, res, 200, indexHtml, 'text/html; charset=utf-8');
  if (url.pathname === '/app.js') return send(req, res, 200, appJs, 'application/javascript; charset=utf-8');
  return send(req, res, 404, notFound, 'text/plain; charset=utf-8');
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`DebtRecover synthetic demo listening on ${PORT} [canonical-files-v2]`);
});

function shutdown(signal) {
  console.log(`DebtRecover synthetic demo shutting down on ${signal}`);
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(1), 5000).unref();
}
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
