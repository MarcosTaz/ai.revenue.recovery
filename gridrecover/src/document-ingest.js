'use strict';

const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const { TextDecoder } = require('util');

const SUPPORTED_EXTENSIONS = new Set(['.pdf', '.txt', '.md', '.csv', '.json']);

function sha256Bytes(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex');
}

function buildLocators(text, sourceSha, paginated = false) {
  const pages = paginated ? text.split('\f') : [text];
  const locators = [];
  pages.forEach((pageText, pageIndex) => {
    pageText.split(/\r?\n/).forEach((line, lineIndex) => {
      const normalized = line.trim();
      if (!normalized) return;
      locators.push({ page: paginated ? pageIndex + 1 : null, line: lineIndex + 1, text: normalized, source_sha256: sourceSha });
    });
  });
  return locators;
}

function decodeUtf8(bytes) {
  try { return new TextDecoder('utf-8', { fatal: true }).decode(bytes); }
  catch { throw new Error('DOCUMENT_UTF8_INVALID'); }
}

function extractPdf(filePath, bytes) {
  if (!bytes.subarray(0, 5).equals(Buffer.from('%PDF-'))) throw new Error('PDF_SIGNATURE_INVALID');
  try {
    return execFileSync('pdftotext', ['-layout', filePath, '-'], {
      encoding: 'utf8', maxBuffer: 10 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe']
    });
  } catch (error) {
    if (error && error.code === 'ENOENT') throw new Error('PDF_EXTRACTOR_UNAVAILABLE');
    throw new Error('PDF_EXTRACTION_FAILED');
  }
}

function extractFromFile(filePath, bytes) {
  const ext = path.extname(filePath).toLowerCase();
  if (!SUPPORTED_EXTENSIONS.has(ext)) throw new Error('DOCUMENT_TYPE_UNSUPPORTED');
  if (ext === '.pdf') return { text: extractPdf(filePath, bytes), extractionMethod: 'pdftotext-layout', paginated: true };
  return { text: decodeUtf8(bytes), extractionMethod: 'utf8-direct', paginated: false };
}

function assemble(documentId, documentType, bytes, extracted) {
  if (!bytes.length) throw new Error('DOCUMENT_EMPTY');
  const sourceSha = sha256Bytes(bytes);
  if (!extracted.text || !extracted.text.trim()) throw new Error('DOCUMENT_TEXT_EMPTY');
  const locators = buildLocators(extracted.text, sourceSha, extracted.paginated);
  if (!locators.length) throw new Error('DOCUMENT_LOCATORS_EMPTY');
  return {
    document_id: documentId,
    document_type: documentType,
    source_sha256: sourceSha,
    byte_length: bytes.length,
    extraction_method: extracted.extractionMethod,
    extracted_text: extracted.text,
    extracted_text_source_sha256: sourceSha,
    locators
  };
}

function ingestDocument({ filePath, documentId, documentType }) {
  if (!filePath || !documentId || !documentType) throw new Error('DOCUMENT_METADATA_REQUIRED');
  const bytes = fs.readFileSync(filePath);
  return assemble(documentId, documentType, bytes, extractFromFile(filePath, bytes));
}

function ingestDocumentBytes({ bytes, fileExtension, documentId, documentType }) {
  if (!documentId || !documentType || !fileExtension) throw new Error('DOCUMENT_METADATA_REQUIRED');
  if (!Buffer.isBuffer(bytes)) bytes = Buffer.from(bytes || []);
  if (!bytes.length) throw new Error('DOCUMENT_EMPTY');
  const ext = String(fileExtension).toLowerCase();
  if (!SUPPORTED_EXTENSIONS.has(ext)) throw new Error('DOCUMENT_TYPE_UNSUPPORTED');
  if (ext !== '.pdf') {
    return assemble(documentId, documentType, bytes, { text: decodeUtf8(bytes), extractionMethod: 'utf8-direct', paginated: false });
  }

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'gridrecover-pdf-'));
  const file = path.join(dir, 'source.pdf');
  try {
    fs.writeFileSync(file, bytes, { mode: 0o600 });
    fs.chmodSync(file, 0o600);
    return assemble(documentId, documentType, bytes, { text: extractPdf(file, bytes), extractionMethod: 'pdftotext-layout', paginated: true });
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

module.exports = { ingestDocument, ingestDocumentBytes, sha256Bytes, buildLocators, SUPPORTED_EXTENSIONS };
