// ICS feed parsing — pure functions, no DOM.
// Extracted verbatim from main.ts (one-shell decomposition).

export function unfoldICS(text: string): string[] {
  return text.replace(/\r\n/g, '\n').split('\n').reduce((lines: string[], line: string) => {
    if (line.startsWith(' ') && lines.length) {
      lines[lines.length - 1] += line.slice(1);
    } else {
      lines.push(line);
    }
    return lines;
  }, [] as string[]);
}

// Parse every VEVENT into a Map keyed by YYYYMMDD — the preview, night
// choghadiya (needs tomorrow's sunrise) and upcoming list all read from it.
export function parseEvents(text: string): Map<string, { summary: string; description: string }> {
  const lines = unfoldICS(text);
  const events = new Map();
  let current: string[] | null = null;
  for (const line of lines) {
    if (line === 'BEGIN:VEVENT') { current = []; continue; }
    if (line === 'END:VEVENT') {
      if (current) {
        const dtstart = current.find(l => l.startsWith('DTSTART;VALUE=DATE:'));
        if (dtstart) {
          const summary = (current.find(l => l.startsWith('SUMMARY:')) || '').slice('SUMMARY:'.length);
          const descLine = current.find(l => l.startsWith('DESCRIPTION:')) || '';
          const description = descLine.slice('DESCRIPTION:'.length)
            .replace(/\\n/g, '\n')
            .replace(/\\,/g, ',')
            .replace(/\\;/g, ';')
            .replace(/\\\\/g, '\\');
          events.set(dtstart.slice('DTSTART;VALUE=DATE:'.length), { summary, description });
        }
      }
      current = null;
      continue;
    }
    if (current) current.push(line);
  }
  return events;
}

