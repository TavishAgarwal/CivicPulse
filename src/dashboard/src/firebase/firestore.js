/**
 * CivicPulse — Firestore Service Layer
 * All Firestore reads/writes for wards, dispatches, volunteers, signals.
 */
import {
  collection, doc, getDoc, getDocs, setDoc, updateDoc, deleteDoc,
  query, where, orderBy, limit, onSnapshot, serverTimestamp,
  addDoc, Timestamp
} from 'firebase/firestore';
import { db } from './config';

// ── Cities & Wards ─────────────────────────────────────────

export function subscribeToCityWards(cityId, callback) {
  const wardsRef = collection(db, 'cities', cityId, 'wards');
  const q = query(wardsRef, orderBy('currentCSS', 'desc'));
  return onSnapshot(q, (snapshot) => {
    const wards = snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
    callback(wards);
  });
}

export async function getAllWards(cityId) {
  const wardsRef = collection(db, 'cities', cityId, 'wards');
  const q = query(wardsRef, orderBy('currentCSS', 'desc'));
  const snapshot = await getDocs(q);
  return snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
}

export async function getWardDetail(cityId, wardId) {
  const wardRef = doc(db, 'cities', cityId, 'wards', wardId);
  const snapshot = await getDoc(wardRef);
  if (!snapshot.exists()) return null;
  return { id: snapshot.id, ...snapshot.data() };
}

export async function getWardHistory(cityId, wardId) {
  const historyRef = collection(db, 'cities', cityId, 'wards', wardId, 'cssHistory');
  const q = query(historyRef, orderBy('computedAt', 'desc'), limit(30));
  const snapshot = await getDocs(q);
  return snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
}

// ── Volunteers ─────────────────────────────────────────────

export async function getVolunteers(filters = {}) {
  let q = query(collection(db, 'volunteers'));

  if (filters.skill) {
    q = query(q, where('skills', 'array-contains', filters.skill));
  }
  if (filters.available) {
    q = query(q, where('isAvailable', '==', true));
  }

  const snapshot = await getDocs(q);
  return snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
}

export function subscribeToVolunteers(callback) {
  const q = query(collection(db, 'volunteers'), orderBy('fatigueScore', 'asc'));
  return onSnapshot(q, (snapshot) => {
    const volunteers = snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
    callback(volunteers);
  });
}

export async function updateVolunteer(volunteerId, data) {
  const volRef = doc(db, 'volunteers', volunteerId);
  await updateDoc(volRef, { ...data, updatedAt: serverTimestamp() });
}

// ── Dispatches ─────────────────────────────────────────────

export async function getDispatches(statusFilter = null) {
  let q;
  if (statusFilter) {
    q = query(
      collection(db, 'dispatches'),
      where('status', '==', statusFilter),
      orderBy('dispatchedAt', 'desc')
    );
  } else {
    q = query(collection(db, 'dispatches'), orderBy('dispatchedAt', 'desc'));
  }
  const snapshot = await getDocs(q);
  return snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
}

export function subscribeToDispatches(callback) {
  const q = query(
    collection(db, 'dispatches'),
    orderBy('dispatchedAt', 'desc'),
    limit(50)
  );
  return onSnapshot(q, (snapshot) => {
    const dispatches = snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
    callback(dispatches);
  });
}

export async function createDispatch(dispatchData) {
  const dispatchRef = await addDoc(collection(db, 'dispatches'), {
    ...dispatchData,
    status: 'pending',
    dispatchedAt: serverTimestamp(),
    auditLog: [{
      action: 'created',
      timestamp: new Date().toISOString(),
      by: dispatchData.createdBy || 'system',
    }],
  });
  return dispatchRef.id;
}

export async function confirmDispatch(dispatchId, confirmedBy) {
  const dispatchRef = doc(db, 'dispatches', dispatchId);
  const snapshot = await getDoc(dispatchRef);
  const existing = snapshot.data();

  await updateDoc(dispatchRef, {
    status: 'confirmed',
    confirmedAt: serverTimestamp(),
    auditLog: [
      ...(existing.auditLog || []),
      { action: 'confirmed', timestamp: new Date().toISOString(), by: confirmedBy },
    ],
  });
}

export async function updateDispatchStatus(dispatchId, status, userId) {
  const dispatchRef = doc(db, 'dispatches', dispatchId);
  const snapshot = await getDoc(dispatchRef);
  const existing = snapshot.data();

  await updateDoc(dispatchRef, {
    status,
    updatedAt: serverTimestamp(),
    auditLog: [
      ...(existing.auditLog || []),
      { action: status, timestamp: new Date().toISOString(), by: userId },
    ],
  });
}

// ── Signals ────────────────────────────────────────────────

export async function getRecentSignals(wardCode, days = 7) {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);

  const q = query(
    collection(db, 'signals'),
    where('locationPin', '==', wardCode),
    where('timestamp', '>=', Timestamp.fromDate(cutoff)),
    orderBy('timestamp', 'desc'),
    limit(200)
  );
  const snapshot = await getDocs(q);
  return snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
}

// ── Config ─────────────────────────────────────────────────

export async function getConfig() {
  const configRef = doc(db, 'config', 'thresholds');
  const snapshot = await getDoc(configRef);
  return snapshot.exists() ? snapshot.data() : {
    cssStableMax: 30,
    cssElevatedMax: 55,
    cssHighThreshold: 56,
    cssCriticalThreshold: 76,
  };
}

// ── Impact Reports ─────────────────────────────────────────

export async function getImpactMetrics() {
  const dispatches = await getDispatches();
  const volunteers = await getVolunteers();

  const confirmed = dispatches.filter(d => d.status === 'confirmed' || d.status === 'completed');
  const active = dispatches.filter(d => d.status === 'active' || d.status === 'pending');

  const avgCss = dispatches.length > 0
    ? dispatches.reduce((sum, d) => sum + (d.cssAtDispatch || 0), 0) / dispatches.length
    : 0;

  return {
    totalDispatches: dispatches.length,
    confirmedDispatches: confirmed.length,
    activeDispatches: active.length,
    totalVolunteers: volunteers.length,
    availableVolunteers: volunteers.filter(v => v.isAvailable).length,
    avgCssAtDispatch: Math.round(avgCss * 10) / 10,
    responseRate: dispatches.length > 0
      ? Math.round((confirmed.length / dispatches.length) * 100)
      : 0,
  };
}
