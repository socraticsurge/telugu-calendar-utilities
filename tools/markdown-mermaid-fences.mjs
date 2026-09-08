function isFence(line, marker) {
  return line.startsWith(marker) && line.slice(marker.length).trim() === ''
}

export function mermaidDiagrams(source) {
  const diagrams = []
  let lines = null
  for (const rawLine of source.split('\n')) {
    const line = rawLine.endsWith('\r') ? rawLine.slice(0, -1) : rawLine
    if (lines === null) {
      if (isFence(line, '```mermaid')) lines = []
      continue
    }
    if (isFence(line, '```')) {
      diagrams.push(lines.join('\n'))
      lines = null
      continue
    }
    lines.push(line)
  }
  return diagrams
}
