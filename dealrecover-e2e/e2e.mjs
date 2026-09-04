import http from 'node:http';
import crypto from 'node:crypto';

const base=process.env.TARGET_BASE;
const tokenA=process.env.TOKEN_A, tenantA=process.env.TENANT_A;
const tokenB=process.env.TOKEN_B, tenantB=process.env.TENANT_B;
if(!base||!tokenA||!tenantA||!tokenB||!tenantB) throw new Error('missing E2E environment');
const dealA=crypto.randomUUID(),dealB=crypto.randomUUID(),docA=crypto.randomUUID();
const results=[];
const headers=(token,tenant,json=true)=>({authorization:`Bearer ${token}`,'x-tenant-id':tenant,...(json?{'content-type':'application/json'}:{})});
async function test(name,path,opts,expected){
  try{const r=await fetch(base+path,opts);const buf=Buffer.from(await r.arrayBuffer());const body=buf.toString('utf8');const row={name,status:r.status,expected,body:body.slice(0,300)};results.push(row);console.log(JSON.stringify(row));if(r.status!==expected)throw new Error(`${name}: expected ${expected}, got ${r.status}`);return {r,buf,body};}
  catch(e){console.error(JSON.stringify({name,error:String(e)}));throw e;}
}
await test('health','/health',{},200);
await test('ready','/ready',{},200);
await test('create_a','/api/deals',{method:'POST',headers:headers(tokenA,tenantA),body:JSON.stringify({dealId:dealA,counterparty:'Synthetic Seller A',currency:'EUR'})},201);
await test('create_b','/api/deals',{method:'POST',headers:headers(tokenB,tenantB),body:JSON.stringify({dealId:dealB,counterparty:'Synthetic Seller B',currency:'USD'})},201);
await test('read_a',`/api/deals/${dealA}`,{headers:headers(tokenA,tenantA)},200);
await test('read_b',`/api/deals/${dealB}`,{headers:headers(tokenB,tenantB)},200);
await test('cross_read_a_as_b',`/api/deals/${dealA}`,{headers:headers(tokenB,tenantB)},404);
await test('cross_read_b_as_a',`/api/deals/${dealB}`,{headers:headers(tokenA,tenantA)},404);
await test('spoof_token_a_tenant_b',`/api/deals/${dealB}`,{headers:headers(tokenA,tenantB)},401);
await test('spoof_token_b_tenant_a',`/api/deals/${dealA}`,{headers:headers(tokenB,tenantA)},401);
const plaintext=`DEALRECOVER-E2E-${crypto.randomUUID()}`;
await test('put_doc_a',`/api/deals/${dealA}/documents/${docA}/content`,{method:'PUT',headers:{...headers(tokenA,tenantA,false),'x-document-type':'CLOSING_STATEMENT','content-type':'application/octet-stream'},body:plaintext},201);
const got=await test('get_doc_a',`/api/deals/${dealA}/documents/${docA}/content`,{headers:headers(tokenA,tenantA,false)},200);
if(got.body!==plaintext)throw new Error('document plaintext roundtrip mismatch');
await test('cross_doc_a_as_b',`/api/deals/${dealA}/documents/${docA}/content`,{headers:headers(tokenB,tenantB,false)},404);
await test('invalid_currency_binding',`/api/deals/${dealA}/analyze`,{method:'POST',headers:headers(tokenA,tenantA),body:JSON.stringify({transactionId:dealA,currency:'USD'})},422);
const summary={result:'PASS',tests:results.length,dealA,dealB,docA};
console.log(JSON.stringify({summary}));
const port=Number(process.env.PORT||3000);
http.createServer((req,res)=>{if(req.url==='/health'){res.writeHead(200,{'content-type':'application/json'});return res.end(JSON.stringify(summary));}res.writeHead(404);res.end();}).listen(port,'0.0.0.0');
