/**
 * CivicPulse — Auth Context (Firebase)
 * Firebase Auth integration with Firestore user profiles.
 * Supports email/password login, registration, and demo mode.
 */
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
} from 'firebase/auth';
import { doc, getDoc, setDoc, serverTimestamp } from 'firebase/firestore';
import { auth, db } from '../firebase/config';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  /* Listen to Firebase Auth state changes */
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        /* Fetch Firestore user profile for role */
        try {
          const userDoc = await getDoc(doc(db, 'users', firebaseUser.uid));
          const profile = userDoc.exists() ? userDoc.data() : {};
          setUser({
            id: firebaseUser.uid,
            email: firebaseUser.email,
            role: profile.role || 'coordinator',
            displayName: profile.displayName || firebaseUser.email?.split('@')[0],
            demo: false,
          });
        } catch {
          /* Firestore may be unreachable — use basic info */
          setUser({
            id: firebaseUser.uid,
            email: firebaseUser.email,
            role: 'coordinator',
            displayName: firebaseUser.email?.split('@')[0],
            demo: false,
          });
        }
      } else {
        setUser(null);
      }
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  /* Login with Firebase Auth */
  const login = useCallback(async (email, password) => {
    try {
      const credential = await signInWithEmailAndPassword(auth, email, password);
      return { data: { uid: credential.user.uid } };
    } catch (err) {
      /* If Firebase Auth fails (misconfigured), allow demo mode */
      if (err.code === 'auth/network-request-failed' || err.code === 'auth/internal-error') {
        console.warn('[CivicPulse] Firebase Auth unavailable — using demo mode');
        demoLogin('coordinator');
        return { demo: true };
      }
      throw err;
    }
  }, []);

  /* Register with Firebase Auth + Firestore profile */
  const register = useCallback(async (email, password, role = 'coordinator') => {
    const credential = await createUserWithEmailAndPassword(auth, email, password);
    /* Create Firestore user profile */
    await setDoc(doc(db, 'users', credential.user.uid), {
      email,
      role,
      displayName: email.split('@')[0],
      createdAt: serverTimestamp(),
    });
    return { data: { uid: credential.user.uid } };
  }, []);

  /* Demo login — bypasses Firebase Auth for offline/demo use */
  const demoLogin = useCallback((role = 'coordinator') => {
    const email = role === 'coordinator'
      ? 'coordinator@civicpulse.demo'
      : 'viewer@civicpulse.demo';
    setUser({
      id: 'demo-user-001',
      email,
      role,
      displayName: role === 'coordinator' ? 'Demo Coordinator' : 'Demo Viewer',
      demo: true,
    });
  }, []);

  /* Logout */
  const logout = useCallback(async () => {
    try {
      await signOut(auth);
    } catch {
      /* Offline — just clear local state */
    }
    setUser(null);
  }, []);

  const isCoordinator = user?.role === 'coordinator';
  const value = {
    user,
    loading,
    login,
    register,
    demoLogin,
    logout,
    isAuthenticated: !!user,
    isCoordinator,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
