function simpleMarkdownParse(mdText) {
  if (!mdText) return '';
  // Escape HTML special characters
  const escapeHtml = (str) => str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  let html = escapeHtml(mdText);

  // Headings ###, ##, #
  html = html.replace(/^###\s+(.*)$/gm, '<h3>$1</h3>');
  html = html.replace(/^##\s+(.*)$/gm, '<h2>$1</h2>');
  html = html.replace(/^#\s+(.*)$/gm, '<h1>$1</h1>');

  // Bold **text** or __text__
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

  // Italic *text* or _text_
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  html = html.replace(/_(.+?)_/g, '<em>$1</em>');

  // Inline code `code`
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Unordered lists
  html = html.replace(/^(?:-|\*)\s+(.*)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, function(match) {
    return '<ul>' + match.trim() + '</ul>\n';
  });

  // Paragraphs
  html = html.replace(/^(?!<h\d|<ul|<li|<\/li|<\/ul)(.+)$/gm, '<p>$1</p>');

  // Line breaks: two spaces at end of line or two newlines
  html = html.replace(/\n{2,}/g, '<br/>\n');

  return html;
}
