const ident=/^[A-Za-z0-9._-]{1,120}$/;
const roleName=x=>{if(!/^[A-Za-z_][A-Za-z0-9_]{0,62}$/.test(x||''))throw new Error('runtime role invalid');return x};
const safe=(x,n)=>{if(!ident.test(x||''))throw new Error(`${n} invalid`);return x};
const asBuffer=x=>Buffer.isBuffer(x)?x:Buffer.from(x);
const parseKey=key=>{
  if(typeof key!=='string')throw new Error('storage key invalid');
  const p=key.split('/');
  if(p.length!==4||p[0]!=='documents'||!p[3].endsWith('.drv'))throw new Error('storage key invalid');
  return {tenantId:safe(p[1],'tenantId'),dealId:safe(p[2],'dealId'),documentId:safe(p[3].slice(0,-4),'documentId')};
};
export class PostgresBlobStore{
  #pool;#role;
  constructor({pool,runtimeRole='dealrecover_rls'}){if(!pool||typeof pool.connect!=='function')throw new Error('pool required');this.#pool=pool;this.#role=roleName(runtimeRole)}
  async #tenant(tenantId,fn){const c=await this.#pool.connect();try{await c.query('begin');await c.query(`set local role ${this.#role}`);await c.query("select set_config('app.tenant_id',$1,true)",[tenantId]);const out=await fn(c);await c.query('commit');return out}catch(e){try{await c.query('rollback')}catch{}throw e}finally{c.release?.()}}
  async putObject({key,body,contentType='application/octet-stream'}){const ids=parseKey(key),bytes=asBuffer(body);if(bytes.length<32)throw new Error('ciphertext too short');await this.#tenant(ids.tenantId,c=>c.query('insert into document_blobs(tenant_id,deal_id,document_id,storage_key,ciphertext,content_type) values($1,$2,$3,$4,$5,$6)',[ids.tenantId,ids.dealId,ids.documentId,key,bytes,contentType]));return {key}}
  async getObject({key}){const ids=parseKey(key);return this.#tenant(ids.tenantId,async c=>{const row=(await c.query('select ciphertext from document_blobs where deal_id=$1 and document_id=$2 and storage_key=$3',[ids.dealId,ids.documentId,key])).rows[0];if(!row)throw Object.assign(new Error('blob not found'),{status:404});return {body:asBuffer(row.ciphertext)}})}
}
export {parseKey as parsePostgresBlobKey};
