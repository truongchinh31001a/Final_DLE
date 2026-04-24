import { getApps, initializeApp } from 'firebase/app';
import {
  EmailAuthProvider,
  GoogleAuthProvider,
  createUserWithEmailAndPassword,
  getAuth,
  linkWithCredential,
  onAuthStateChanged,
  signInWithPopup,
  signOut,
} from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID,
};

const firebaseAuthEnabled = Boolean(
  firebaseConfig.apiKey &&
  firebaseConfig.authDomain &&
  firebaseConfig.projectId &&
  firebaseConfig.appId
);

const app = firebaseAuthEnabled
  ? (getApps()[0] ?? initializeApp(firebaseConfig))
  : null;

const auth = app ? getAuth(app) : null;
const googleProvider = auth ? new GoogleAuthProvider() : null;

export {
  EmailAuthProvider,
  auth,
  createUserWithEmailAndPassword,
  firebaseAuthEnabled,
  googleProvider,
  linkWithCredential,
  onAuthStateChanged,
  signInWithPopup,
  signOut,
};
