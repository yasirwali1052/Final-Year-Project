// Firebase SDKs import 
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore"; // ✅ Import Firestore
import { GoogleAuthProvider } from "firebase/auth"; // ✅ Add this impor


// Firebase Config with direct credentials
const firebaseConfig = {
  apiKey: "",
  authDomain: "",
  projectId: "",
  storageBucket: "",
  messagingSenderId: "",
  appId: "",
  measurementId: ""
};

// Firebase initialize 
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app); // ✅ Initialize Firestore
const provider = new GoogleAuthProvider(); // ✅ this line

export { auth, db, provider }; // ✅ Now you're exporting the Google provider too


