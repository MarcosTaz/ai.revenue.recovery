import http from 'node:http';

const port=Number(process.env.PORT||3000);
const host=(process.env.HOST||'0.0.0.0').trim();
const sourceDigest='d7de699c757797aa3d275e6d21757cbe74b4ee26e59fa01cd801f35638df4a04';
const build='0.7.1';
const json=(res,status,data)=>{
  res.statusCode=status;
  res.setHeader('content-type','application/json');
  res.setHeader('cache-control','no-store');
  res.setHeader('content-security-policy',"default-src 'none'; frame-ancestors 'none'; base-uri 'none'");
  res.setHeader('x-content-type-options','nosniff');
  res.setHeader('referrer-policy','no-referrer');
  res.setHeader('permissions-policy','camera=(), microphone=(), geolocation=()');
  res.setHeader('cross-origin-resource-policy','same-origin');
  res.setHeader('cross-origin-opener-policy','same-origin');
  res.setHeader('x-frame-options','DENY');
  res.end(JSON.stringify(data));
};

const server=http.createServer((req,res)=>{
  const u=new URL(req.url,'http://local');
  if(req.method==='GET'&&u.pathname==='/health')return json(res,200,{ok:true,service:'dealrecover',build,sourceDigest,deployMode:'health-only'});
  if(req.method==='GET'&&u.pathname==='/ready')return json(res,503,{ready:false,service:'dealrecover',build,reason:'managed runtime not activated'});
  return json(res,503,{error:'managed runtime not ready'});
});
server.listen(port,host);
const close=()=>server.close(()=>process.exit(0));
process.on('SIGTERM',close);
process.on('SIGINT',close);
