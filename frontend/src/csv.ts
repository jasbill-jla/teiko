// Quotes a field only if it needs it (contains a comma, quote, or newline),
// doubling any internal quotes -- standard CSV escaping (RFC 4180).
function csvField(value: string | number | null): string {
  const text = value === null ? '' : String(value)
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`
  }
  return text
}

export function toCsv(columns: string[], rows: Array<Array<string | number | null>>): string {
  const lines = [columns.map(csvField).join(',')]
  for (const row of rows) {
    lines.push(row.map(csvField).join(','))
  }
  return lines.join('\r\n')
}

export function downloadCsv(filename: string, csv: string): void {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
