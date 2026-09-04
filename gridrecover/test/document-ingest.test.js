'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { ingestDocument, ingestDocumentBytes, sha256Bytes } = require('../src/document-ingest');

const PDF_B64 = 'JVBERi0xLjMKJZOMi54gUmVwb3J0TGFiIEdlbmVyYXRlZCBQREYgZG9jdW1lbnQgKG9wZW5zb3VyY2UpCjEgMCBvYmoKPDwKL0YxIDIgMCBSCj4+CmVuZG9iagoyIDAgb2JqCjw8Ci9CYXNlRm9udCAvSGVsdmV0aWNhIC9FbmNvZGluZyAvV2luQW5zaUVuY29kaW5nIC9OYW1lIC9GMSAvU3VidHlwZSAvVHlwZTEgL1R5cGUgL0ZvbnQKPj4KZW5kb2JqCjMgMCBvYmoKPDwKL0NvbnRlbnRzIDcgMCBSIC9NZWRpYUJveCBbIDAgMCA2MTIgNzkyIF0gL1BhcmVudCA2IDAgUiAvUmVzb3VyY2VzIDw8Ci9Gb250IDEgMCBSIC9Qcm9jU2V0IFsgL1BERiAvVGV4dCAvSW1hZ2VCIC9JbWFnZUMgL0ltYWdlSSBdCj4+IC9Sb3RhdGUgMCAvVHJhbnMgPDwKCj4+IAogIC9UeXBlIC9QYWdlCj4+CmVuZG9iago0IDAgb2JqCjw8Ci9QYWdlTW9kZSAvVXNlTm9uZSAvUGFnZXMgNiAwIFIgL1R5cGUgL0NhdGFsb2cKPj4KZW5kb2JqCjUgMCBvYmoKPDwKL0F1dGhvciAoYW5vbnltb3VzKSAvQ3JlYXRpb25EYXRlIChEOjIwMjYwODI5MjA0ODUyKzAwJzAwJykgL0NyZWF0b3IgKGFub255bW91cykgL0tleXdvcmRzICgpIC9Nb2REYXRlIChEOjIwMjYwODI5MjA0ODUyKzAwJzAwJykgL1Byb2R1Y2VyIChSZXBvcnRMYWIgUERGIExpYnJhcnkgLSBcKG9wZW5zb3VyY2VcKSkgCiAgL1N1YmplY3QgKHVuc3BlY2lmaWVkKSAvVGl0bGUgKHVudGl0bGVkKSAvVHJhcHBlZCAvRmFsc2UKPj4KZW5kb2JqCjYgMCBvYmoKPDwKL0NvdW50IDEgL0tpZHMgWyAzIDAgUiBdIC9UeXBlIC9QYWdlcwo+PgplbmRvYmoKNyAwIG9iago8PAovRmlsdGVyIFsgL0FTQ0lJODVEZWNvZGUgL0ZsYXRlRGVjb2RlIF0gL0xlbmd0aCAxNzkKPj4Kc3RyZWFtCkdhclcwNW1yOTAnU1ByU01FK15tYnBObWlYWXBjZUAhZCVSb0cqW1xYP3VSSj5IMSZHUXNnS0JIcGBeQmthYzhtLy9lJGdKSi5HaVVtMi0jMEg+ZTxePSxMYCoucUhoMTdQSkw9bV82aEskQmxhQTlnMz4/YnMnNTw7YEZmNUxzQmorQXVBVFtQQyY3cmU8ZGluWkojVT9AKT9eViZPRHBLL0BddWxLOGkuJFxbQ2g/Tn4+ZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgOAowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwNjEgMDAwMDAgbiAKMDAwMDAwMDA5MiAwMDAwMCBuIAowMDAwMDAwMTk5IDAwMDAwIG4gCjAwMDAwMDAzOTIgMDAwMDAgbiAKMDAwMDAwMDQ2MCAwMDAwMCBuIAowMDAwMDAwNzIxIDAwMDAwIG4gCjAwMDAwMDA3ODAgMDAwMDAgbiAKdHJhaWxlcgo8PAovSUQgCls8Mzk1ODAxYmZkNDhkOGQwNTY4YTdkY2Y4MTZlOGUwYTk+PDM5NTgwMWJmZDQ4ZDhkMDU2OGE3ZGNmODE2ZThlMGE5Pl0KJSBSZXBvcnRMYWIgZ2VuZXJhdGVkIFBERiBkb2N1bWVudCAtLSBkaWdlc3QgKG9wZW5zb3VyY2UpCgovSW5mbyA1IDAgUgovUm9vdCA0IDAgUgovU2l6ZSA4Cj4+CnN0YXJ0eHJlZgoxMDQ5CiUlRU9GCg==';

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'gridrecover-doc-'));
try {
  const txt = path.join(dir, 'agreement.txt');
  fs.writeFileSync(txt, 'Article 11.4.1\nNetwork Upgrade repayment term\n', 'utf8');
  const txtBytes = fs.readFileSync(txt);
  const t = ingestDocument({ filePath: txt, documentId: 'TXT-1', documentType: 'EXECUTED_LGIA' });
  assert.equal(t.source_sha256, sha256Bytes(txtBytes));
  assert.equal(t.extracted_text_source_sha256, t.source_sha256);
  assert.equal(t.extraction_method, 'utf8-direct');
  assert.equal(t.locators[0].line, 1);
  assert.equal(t.locators[0].source_sha256, t.source_sha256);

  const tb = ingestDocumentBytes({ bytes: txtBytes, fileExtension: '.txt', documentId: 'TXT-BYTES', documentType: 'EXECUTED_LGIA' });
  assert.equal(tb.source_sha256, t.source_sha256);
  assert.equal(tb.locators[1].text, 'Network Upgrade repayment term');

  const pdf = path.join(dir, 'agreement.pdf');
  const pdfBytes = Buffer.from(PDF_B64, 'base64');
  fs.writeFileSync(pdf, pdfBytes);
  const p = ingestDocument({ filePath: pdf, documentId: 'PDF-1', documentType: 'EXECUTED_LGIA' });
  assert.equal(p.source_sha256, sha256Bytes(pdfBytes));
  assert.equal(p.extracted_text_source_sha256, p.source_sha256);
  assert.equal(p.extraction_method, 'pdftotext-layout');
  assert(p.extracted_text.includes('GRIDRECOVER TEST LGIA'));
  assert(p.extracted_text.includes('Article 11.4.1'));
  assert(p.locators.some(l => l.page === 1 && l.source_sha256 === p.source_sha256));

  const pb = ingestDocumentBytes({ bytes: pdfBytes, fileExtension: '.pdf', documentId: 'PDF-BYTES', documentType: 'EXECUTED_LGIA' });
  assert.equal(pb.source_sha256, p.source_sha256);
  assert(pb.extracted_text.includes('Article 11.4.1'));

  const badPdf = path.join(dir, 'bad.pdf');
  fs.writeFileSync(badPdf, 'not a pdf');
  assert.throws(() => ingestDocument({ filePath: badPdf, documentId: 'B', documentType: 'EXECUTED_LGIA' }), /PDF_SIGNATURE_INVALID/);
  assert.throws(() => ingestDocumentBytes({ bytes: Buffer.from('not a pdf'), fileExtension: '.pdf', documentId: 'BB', documentType: 'EXECUTED_LGIA' }), /PDF_SIGNATURE_INVALID/);

  const unsupported = path.join(dir, 'file.bin');
  fs.writeFileSync(unsupported, Buffer.from([1, 2, 3]));
  assert.throws(() => ingestDocument({ filePath: unsupported, documentId: 'U', documentType: 'OTHER' }), /DOCUMENT_TYPE_UNSUPPORTED/);
  assert.throws(() => ingestDocumentBytes({ bytes: Buffer.from('x'), fileExtension: '.bin', documentId: 'UB', documentType: 'OTHER' }), /DOCUMENT_TYPE_UNSUPPORTED/);

  const invalidUtf8 = path.join(dir, 'bad.txt');
  fs.writeFileSync(invalidUtf8, Buffer.from([0xff, 0xfe, 0xfd]));
  assert.throws(() => ingestDocument({ filePath: invalidUtf8, documentId: 'UTF', documentType: 'OTHER' }), /DOCUMENT_UTF8_INVALID/);
  assert.throws(() => ingestDocumentBytes({ bytes: Buffer.from([0xff]), fileExtension: '.txt', documentId: 'UTFB', documentType: 'OTHER' }), /DOCUMENT_UTF8_INVALID/);

  console.log('GRIDRECOVER document ingestion provenance: 22/22 PASS');
} finally {
  fs.rmSync(dir, { recursive: true, force: true });
}
