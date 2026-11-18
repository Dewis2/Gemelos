const key = "gemelos-editor-token";

export function editorToken(): string | null {
  return sessionStorage.getItem(key);
}

export function setEditorToken(token: string): void {
  sessionStorage.setItem(key, token);
  window.dispatchEvent(new Event("editor-session-changed"));
}

export function clearEditorToken(): void {
  sessionStorage.removeItem(key);
  window.dispatchEvent(new Event("editor-session-changed"));
}
