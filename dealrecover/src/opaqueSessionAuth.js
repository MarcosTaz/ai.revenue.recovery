import crypto from 'node:crypto';
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const tokenRe=/^[A-Za-z0-9_-]{43,128}$/;
const fail=(message,status=401)=>Object.assign(new Error(message),{status});
const roleName=x=>{if(!/^[A-Za-z_][A-Za-z0-9_]{0,62}$/.test(x||''))throw new Error('runtime role invalid');return x};
const oneHeader=(headers,name)=>{const v=headers?.[name]??headers?.[name.toLowerCase()];if(Array.isArray(v))return v.length===1?v[0]:null;return typeof v==='string'?v:null};
export function opaqueBearerToken(req){const h=oneHeader(req.headers,'authorization');if(!h||!/^Bearer\s+\S+$/i.test(h))throw fail('bearer token required');const t=h.replace(/^Bearer\s+/i,'');if(!tokenRe.test(t))throw fail('invalid bearer token');return t}
export function opaqueTenantHeader(req){const tenantId=oneHeader(req.headers,'x-tenant-id');if(!tenantId||!uuid.test(tenantId))throw fail('valid x-tenant-id required');return tenantId}
export const hashOpaqueToken=token=>crypto.createHash('sha256').update(token).digest('hex');
export function createOpaqueSessionAuthenticator({pool,runtimeRole='dealrecover_rls'}){
  if(!pool||typeof pool.connect!=='function')throw new Error('pool required');const rr=roleName(runtimeRole);
  return async req=>{const token=opaqueBearerToken(req),tenantId=opaqueTenantHeader(req),hash=hashOpaqueToken(token),c=await pool.connect();let row;try{await c.query('begin');await c.query(`set local role ${rr}`);await c.query("select set_config('app.tenant_id',$1,true)",[tenantId]);row=(await c.query('select user_id,expires_at,verification_ref from api_sessions where token_hash=$1 and revoked_at is null and expires_at>now()',[hash])).rows[0];await c.query('commit')}catch(e){try{await c.query('rollback')}catch{}throw e}finally{c.release?.()}if(!row)throw fail('invalid or expired session');if(!uuid.test(row.user_id))throw fail('invalid session identity');if(!row.verification_ref)throw fail('session verification evidence missing',403);return {user:{id:row.user_id,emailVerified:true,banned:false},session:{activeOrganizationId:tenantId,expiresAt:new Date(row.expires_at).toISOString(),impersonatedBy:null}}}
}
