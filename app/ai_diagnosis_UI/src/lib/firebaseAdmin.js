import admin from 'firebase-admin';

function getFirebaseServiceAccount() {
  const rawConfig = process.env.FIREBASE_SERVICE_ACCOUNT_KEY_PATH;
  if (!rawConfig) {
    throw new Error('FIREBASE_SERVICE_ACCOUNT_KEY_PATH is not set');
  }

  try {
    return JSON.parse(rawConfig);
  } catch (error) {
    throw new Error('FIREBASE_SERVICE_ACCOUNT_KEY_PATH must be valid JSON');
  }
}

function getFirebaseAdminApp() {
  if (!admin.apps.length) {
    admin.initializeApp({
      credential: admin.credential.cert(getFirebaseServiceAccount()),
    });
  }

  return admin.app();
}

export function getAdminAuth() {
  return getFirebaseAdminApp().auth();
}

export async function verifyTokenAndGetUserId(authHeader) {
  if (!authHeader) {
    throw new Error('No Authorization header provided');
  }

  const token = authHeader.split(' ')[1];
  try {
    const decodedToken = await getAdminAuth().verifyIdToken(token);
    return decodedToken.uid;
  } catch (error) {
    console.error('Error verifying token:', error.message);
    throw new Error('Invalid or expired token');
  }
}
