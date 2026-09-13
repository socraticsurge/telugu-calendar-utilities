let lastMuhurtaResult = null;

export function getMuhurtaResult() {
  return lastMuhurtaResult;
}

export function setMuhurtaResult(result): void {
  lastMuhurtaResult = result;
}

export function clearMuhurtaResult(): void {
  lastMuhurtaResult = null;
}

export function hasMuhurtaResult(): boolean {
  return Boolean(lastMuhurtaResult);
}
