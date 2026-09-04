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
  try{const r=await fetch(base+path,opts);const buf=Buffer.from(await r.arrayBuffer());const body=buf.toString('utf8');const row={name,status:r.status,expected,body:body.slice(0,400)};results.push(row);console.log(JSON.stringify(row));if(r.status!==expected)throw new Error(`${name}: expected ${expected}, got ${r.status}`);return {r,buf,body};}
  catch(e){console.error(JSON.stringify({name,error:String(e)}));throw e;}
}
const post=(name,path,token,tenant,payload,expected=200)=>test(name,path,{method:'POST',headers:headers(token,tenant),body:JSON.stringify(payload)},expected);
const ev=ref=>({state:'VERIFIED',refs:[ref]});

await test('health','/health',{},200);
await test('ready','/ready',{},200);
await post('create_a','/api/deals',tokenA,tenantA,{dealId:dealA,counterparty:'Synthetic Seller A',currency:'EUR'},201);
await post('create_b','/api/deals',tokenB,tenantB,{dealId:dealB,counterparty:'Synthetic Seller B',currency:'USD'},201);
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
await post('invalid_currency_binding',`/api/deals/${dealA}/analyze`,tokenA,tenantA,{transactionId:dealA,currency:'USD'},422);

const wc={
  transactionId:dealA,currency:'EUR',asOf:'2026-09-04',
  documents:[{id:'SPA-1',type:'SPA',signed:true,effectiveDate:'2026-01-01',sequence:1,evidence:ev('spa-signed'),terms:{WorkingCapital:{clause:'2.1'},TargetWorkingCapital:{clause:'2.2',value:100},ClosingWorkingCapital:{clause:'2.3'},AccountingPrinciples:{clause:'Schedule 4'},CalculationTime:{clause:'2.4',value:'2026-08-31'}}}],
  policies:[{id:'P-AR',level:'EXPRESS_SPA',account:'AR',treatment:'INCLUDE_ASSET',evidence:ev('policy-ar')},{id:'P-AP',level:'EXPRESS_SPA',account:'AP',treatment:'INCLUDE_LIABILITY',evidence:ev('policy-ap')}],
  lines:[{id:'L-AR',transactionId:dealA,currency:'EUR',periodEnd:'2026-08-31',sourceRef:'GL-AR',account:'AR',amount:180,evidence:ev('gl-ar')},{id:'L-AP',transactionId:dealA,currency:'EUR',periodEnd:'2026-08-31',sourceRef:'GL-AP',account:'AP',amount:60,evidence:ev('gl-ap')}],
  actualAdjustment:10,actualAdjustmentEvidence:ev('closing-actual-adjustment'),closingStatementEvidence:ev('closing-statement'),closingStatementControlTotal:120,
  deadline:{type:'EXPLICIT_DATE',date:'2026-12-31',evidence:ev('spa-dispute-deadline')}
};
const analyzed=await post('positive_wc_analysis',`/api/deals/${dealA}/analyze`,tokenA,tenantA,wc,200);
const analyzedJson=JSON.parse(analyzed.body);
if(analyzedJson.result?.state!=='SUPPORTED'||analyzedJson.result?.calculation?.difference!==10||analyzedJson.dossier?.digest!==analyzedJson.result?.digest)throw new Error('positive WC analysis/dossier invariant failed');
const analysisDigest=analyzedJson.result.digest;

await post('dispute_reviewed',`/api/deals/${dealA}/dispute`,tokenA,tenantA,{status:'REVIEWED',note:'Synthetic human review complete'},200);
await post('dispute_notice_prepared',`/api/deals/${dealA}/dispute`,tokenA,tenantA,{status:'NOTICE_PREPARED',note:'Synthetic notice prepared'},200);
await post('dispute_submitted',`/api/deals/${dealA}/dispute`,tokenA,tenantA,{status:'SUBMITTED_EXTERNALLY',note:'Synthetic submission evidence recorded'},200);
await post('dispute_resolved',`/api/deals/${dealA}/dispute`,tokenA,tenantA,{status:'RESOLVED',note:'Synthetic economic resolution'},200);

const outcomeDigest=crypto.createHash('sha256').update(`synthetic-bank-evidence:${dealA}`).digest('hex');
await post('outcome_recovered',`/api/deals/${dealA}/outcome`,tokenA,tenantA,{kind:'RECOVERED',amount:10,currency:'EUR',evidenceDigest:outcomeDigest,evidenceRefs:['synthetic-bank-credit']},200);
await post('billing_draft',`/api/deals/${dealA}/billing`,tokenA,tenantA,{status:'DRAFT',amount:2.5,currency:'EUR'},200);
await post('billing_approved',`/api/deals/${dealA}/billing`,tokenA,tenantA,{status:'APPROVED_TO_INVOICE',amount:2.5,currency:'EUR'},200);
await post('billing_invoiced',`/api/deals/${dealA}/billing`,tokenA,tenantA,{status:'INVOICED_EXTERNALLY',amount:2.5,currency:'EUR'},200);
await post('billing_paid',`/api/deals/${dealA}/billing`,tokenA,tenantA,{status:'PAID_EXTERNALLY',amount:2.5,currency:'EUR',paymentEvidenceRefs:['synthetic-payment-evidence']},200);

const finalSnap=await test('final_snapshot',`/api/deals/${dealA}`,{headers:headers(tokenA,tenantA)},200);
const snap=JSON.parse(finalSnap.body);
if(snap.dispute?.state!=='RESOLVED'||snap.outcome?.outcome!=='RECOVERED'||Number(snap.outcome?.amount)!==10||snap.billing?.status!=='PAID_EXTERNALLY'||snap.documents?.length!==1)throw new Error('final commercial lifecycle snapshot mismatch');
await test('cross_final_snapshot',`/api/deals/${dealA}`,{headers:headers(tokenB,tenantB)},404);

const analysisGet=await test('analysis_retrieval',`/api/deals/${dealA}/analyses/${analysisDigest}`,{headers:headers(tokenA,tenantA)},200);
const analysisRow=JSON.parse(analysisGet.body);
if(analysisRow.digest!==analysisDigest||analysisRow.payload?.state!=='SUPPORTED'||analysisRow.payload?.calculation?.difference!==10)throw new Error('analysis retrieval invariant failed');
const dossierGet=await test('dossier_retrieval',`/api/deals/${dealA}/dossiers/${analysisDigest}`,{headers:headers(tokenA,tenantA)},200);
const dossierRow=JSON.parse(dossierGet.body);
if(dossierRow.digest!==analysisDigest||dossierRow.payload?.schema!=='dealrecover-ppa-dossier-v2'||dossierRow.payload?.digest!==analysisDigest)throw new Error('dossier retrieval invariant failed');
await test('cross_analysis_retrieval',`/api/deals/${dealA}/analyses/${analysisDigest}`,{headers:headers(tokenB,tenantB)},404);
await test('cross_dossier_retrieval',`/api/deals/${dealA}/dossiers/${analysisDigest}`,{headers:headers(tokenB,tenantB)},404);

const auditGet=await test('audit_retrieval',`/api/deals/${dealA}/audit`,{headers:headers(tokenA,tenantA)},200);
const audit=JSON.parse(auditGet.body);
const expectedTypes=['DEAL_CREATED','DOCUMENT_STORED','ANALYSIS_SUPPORTED','DOSSIER_SAVED','DISPUTE_STATE_CHANGED','DISPUTE_STATE_CHANGED','DISPUTE_STATE_CHANGED','DISPUTE_STATE_CHANGED','OUTCOME_RECORDED','BILLING_STATE_CHANGED','BILLING_STATE_CHANGED','BILLING_STATE_CHANGED','BILLING_STATE_CHANGED'];
if(audit.verification?.valid!==true||audit.verification?.count!==expectedTypes.length||audit.events?.length!==expectedTypes.length)throw new Error('audit verification/count failed');
if(audit.events.map(e=>e.eventType).join('|')!==expectedTypes.join('|'))throw new Error('audit event sequence failed');
for(let i=0;i<audit.events.length;i++){
  if(!/^[0-9a-f]{64}$/.test(audit.events[i].eventHash))throw new Error('audit hash format failed');
  if(i===0&&audit.events[i].prevHash!==null)throw new Error('audit genesis failed');
  if(i>0&&audit.events[i].prevHash!==audit.events[i-1].eventHash)throw new Error('audit chain linkage failed');
}
if(audit.verification.headHash!==audit.events.at(-1).eventHash)throw new Error('audit head hash failed');
await test('cross_audit_retrieval',`/api/deals/${dealA}/audit`,{headers:headers(tokenB,tenantB)},404);

const summary={result:'PASS',tests:results.length,dealA,dealB,docA,analysisDigest,recovered:10,billingStatus:'PAID_EXTERNALLY',auditEvents:audit.events.length,auditHead:audit.verification.headHash,dossierSchema:dossierRow.payload.schema};
console.log(JSON.stringify({summary}));
if(process.env.E2E_ONESHOT==='1') process.exit(0);
const port=Number(process.env.PORT||3000);
http.createServer((req,res)=>{if(req.url==='/health'){res.writeHead(200,{'content-type':'application/json'});return res.end(JSON.stringify(summary));}res.writeHead(404);res.end();}).listen(port,'0.0.0.0');
