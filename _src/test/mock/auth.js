export function getAuth() { return {}; }
export class GoogleAuthProvider {}
export async function signInWithPopup() {}
export async function signInWithRedirect() {}
export async function getRedirectResult() { return null; }
export function onAuthStateChanged(a, cb) { setTimeout(() => cb({ email: 'gestore@example.com' }), 10); }
export async function signOut() {}
