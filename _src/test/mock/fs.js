const DB = window.__MOCKDB || (window.__MOCKDB = {});
const col = n => (DB[n] = DB[n] || {});
export class Timestamp { constructor(ms) { this.ms = ms; } toMillis() { return this.ms; } toDate() { return new Date(this.ms); } static now() { return new Timestamp(Date.now()); } static fromDate(d) { return new Timestamp(d.getTime()); } }
export function getFirestore() { return {}; }
export function collection(db, n) { return { n }; }
export function doc(db, c, id) { return { c, id }; }
export async function getDoc(r) { const v = col(r.c)[r.id]; return { exists: () => !!v, data: () => v }; }
export async function getDocs(c) { return { docs: Object.entries(col(c.n)).map(([id, v]) => ({ id, data: () => v })) }; }
export async function setDoc(r, v) { col(r.c)[r.id] = { ...v }; (window.__W = window.__W || []).push(['set', r.c, r.id, v]); }
export async function updateDoc(r, v) { col(r.c)[r.id] = { ...col(r.c)[r.id], ...v }; (window.__W = window.__W || []).push(['upd', r.c, r.id, v]); }
export async function deleteDoc(r) { delete col(r.c)[r.id]; (window.__W = window.__W || []).push(['del', r.c, r.id]); }
