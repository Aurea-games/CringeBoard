export function isOnlyUrl(text) {
  if (!text) return false;
  const trimmed = String(text).trim();
  // simple URL-only detection: starts with http(s):// or www. and contains no whitespace
  // If the text explicitly contains labels like "Article URL:" or "Comments URL:",
  // consider it a URL-only description as well.
  const lower = trimmed.toLowerCase();
  if (lower.includes("article url:") || lower.includes("comments url:")) return true;

  // simple URL-only detection: starts with http(s):// or www. and contains no whitespace
  if (/^(https?:\/\/|www\.)\S+$/i.test(trimmed)) return true;

  // also allow variants like "Article URL: https://..." or "Comments URL: www..."
  if (/^(?:article url:|comments url:)\s*(https?:\/\/|www\.)\S+$/i.test(trimmed))
    return true;

  return false;
}

export function previewText(text, maxLen = 140, fallback = "No description") {
  if (!text) return fallback;
  if (isOnlyUrl(text)) return fallback;
  const s = String(text);
  if (s.length <= maxLen) return s;
  return s.slice(0, maxLen) + "…";
}
