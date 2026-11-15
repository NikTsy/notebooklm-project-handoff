function doPost(e) {
  const respond = (data) => ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
  if (!e || !e.postData || e.contentLength > 150000) return respond({ok: false});

  let request;
  try {
    request = JSON.parse(e.postData.contents);
  } catch (_) {
    return respond({ok: false});
  }
  if (!request || typeof request.text !== 'string' || !request.text.trim() ||
      !Number.isSafeInteger(request.timestamp) || typeof request.signature !== 'string' ||
      Math.abs(Date.now() - request.timestamp) > 120000) return respond({ok: false});

  const properties = PropertiesService.getScriptProperties();
  const secret = properties.getProperty('HANDOFF_SIGNING_KEY');
  const documentId = properties.getProperty('DOCUMENT_ID');
  if (!secret || !documentId) return respond({ok: false});
  const expected = Utilities.computeHmacSha256Signature(
    request.timestamp + '\n' + request.text, secret, Utilities.Charset.UTF_8)
    .map((byte) => (byte & 255).toString(16).padStart(2, '0')).join('');
  if (request.signature.length !== expected.length) return respond({ok: false});
  let difference = 0;
  for (let i = 0; i < expected.length; i++) {
    difference |= expected.charCodeAt(i) ^ request.signature.charCodeAt(i);
  }
  if (difference !== 0) return respond({ok: false});

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    if (request.timestamp <= Number(properties.getProperty('LAST_TIMESTAMP'))) {
      return respond({ok: false});
    }
    const doc = DocumentApp.openById(documentId);
    const body = doc.getBody();
    const text = request.text
      .replace(/^#{1,2} /gm, '')
      .replace(/^- /gm, '• ')
      .replace(/`([^`\n]+)`/g, '$1')
      .trimEnd();
    if (body.getText() !== text) body.setText(text);
    doc.saveAndClose();
    properties.setProperty('LAST_TIMESTAMP', String(request.timestamp));
    return respond({ok: true, signature: expected});
  } finally {
    lock.releaseLock();
  }
}
