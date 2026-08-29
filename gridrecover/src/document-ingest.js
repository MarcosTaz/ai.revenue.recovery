'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { TextDecoder } = require('util');

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
      locators.push({
        page: paginated ? pageIndex + 1 : null,
        line: lineIndex + 1,
        text: normalized,
        source_sha256: sourceSha
      });
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
      encoding: 'utf8',
      maxBuffer: 10 * 1024 * 1024,
      stdio: ['ignore', 'pipe', 'pipe']
    });
  } catch (error) {
    if (error && error.code === 'ENOENT') throw new Error('PDF_EXTRACTOR_UNAVAILABLE');
    throw new Error('PDF_EXTRACTION_FAILED');
  }
}

function ingestDocument({ filePath, documentId, documentType }) {
  if (!filePath || !documentId || !documentType) throw new Error('DOCUMENT_METADATA_REQUIRED');
  const bytes = fs.readFileSync(filePath);
  if (!bytes.length) throw new Error('DOCUMENT_EMPTY');
  const sourceSha = sha256Bytes(bytes);
  const ext = path.extname(filePath).toLowerCase();

  let text;
  let extractionMethod;
  let paginated = false;

  if (ext === '.pdf') {
    text = extractPdf(filePath, bytes);
    extractionMethod = 'pdftotext-layout';
    paginated = true;
  } else if (['.txt', '.md', '.csv', '.json'].includes(ext)) {
    text = decodeUtf8(bytes);
    extractionMethod = 'utf8-direct';
  } else {
    throw new Error('DOCUMENT_TYPE_UNSUPPORTED');
  }

  if (!text || !text.trim()) throw new Error('DOCUMENT_TEXT_EMPTY');
  const locators = buildLocators(text, sourceSha, paginated);
  if (!locators.length) throw new Error('DOCUMENT_LOCATORS_EMPTY');

  return {
    document_id: documentId,
    document_type: documentType,
    source_sha256: sourceSha,
    byte_length: bytes.length,
    extraction_method: extractionMethod,
    extracted_text: text,
    extracted_text_source_sha256: sourceSha,
    locators
  };
}

module.exports = { ingestDocument, sha256Bytes, buildLocators };
