// @vitest-environment node
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { expect, test } from 'vitest';

const rules = resolve('src/scorer/tara-chandra.ts');
const allowed = new Set([
  rules,
  resolve('src/data/rasis.ts'),
  resolve('src/data/shared-calendar-tables.generated.json'),
]);

function checkDependency(path: string, visited: Set<string>): void {
  expect(allowed.has(path), path).toBe(true);
  if (visited.has(path) || path.endsWith('.json')) return;
  visited.add(path);
  const source = readFileSync(path, 'utf8');
  expect(source).not.toMatch(/\b(window|document|localStorage|sessionStorage|fetch|navigator|XMLHttpRequest|WebSocket|globalThis)\b/);
  expect(source).not.toMatch(/\b(?:import|require)\s*\(/);
  const dependencies = source.matchAll(/\b(?:from|import)\s*['"]([^'"]+)['"]/g);
  for (const [, specifier] of dependencies) {
    expect(specifier.startsWith('.')).toBe(true);
    const dependency = resolve(dirname(path), specifier);
    checkDependency(dependency.endsWith('.json') ? dependency : `${dependency}.ts`, visited);
  }
}

test('Tara/Chandra rules and their dependencies need no browser or network', () => {
  checkDependency(rules, new Set());
});

test.each(['muhurta-scoring.ts', 'muhurta-day-rules.ts'])(
  '%s imports the pure rules instead of the UI journey', name => {
    const source = readFileSync(resolve('src/panels', name), 'utf8');
    expect(source).toContain("from '../scorer/tara-chandra'");
    expect(source).not.toContain('tarabalam-journey');
  },
);
