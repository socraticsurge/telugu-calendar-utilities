import { describe, expect, test } from 'vitest';

import { mermaidDiagrams } from '../../tools/markdown-mermaid-fences.mjs';

describe('Mermaid fence extraction', () => {
  test('extracts each complete top-level Mermaid fence without crossing ordinary fences', () => {
    const source = [
      '# Example',
      '```mermaid',
      'flowchart LR',
      '  A --> B',
      '```',
      '```js',
      "const ignored = '```mermaid'",
      '```',
      '```mermaid   ',
      'sequenceDiagram',
      '  A->>B: hello',
      '```   ',
    ].join('\n');

    expect(mermaidDiagrams(source)).toEqual([
      'flowchart LR\n  A --> B',
      'sequenceDiagram\n  A->>B: hello',
    ]);
  });

  test('ignores an unfinished fence', () => {
    expect(mermaidDiagrams('```mermaid\nflowchart LR')).toEqual([]);
  });
});
