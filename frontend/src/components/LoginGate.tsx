import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { setAuthToken, verifyToken } from "../api/client";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

interface LoginGateProps {
  onUnlock: () => void;
}

export default function LoginGate({ onUnlock }: LoginGateProps) {
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(false);
  const buttonRef = useRef<HTMLDivElement>(null);

  const handleCredentialResponse = useCallback(async (response: { credential: string }) => {
    setChecking(true);
    setError("");
    const token = response.credential;
    setAuthToken(token);
    const ok = await verifyToken(token);
    if (ok) {
      onUnlock();
    } else {
      setAuthToken("");
      setError("Your account is not authorized to use this app.");
      setChecking(false);
    }
  }, [onUnlock]);

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = () => {
      window.google?.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleCredentialResponse,
      });
      if (buttonRef.current) {
        window.google?.accounts.id.renderButton(buttonRef.current, {
          theme: "filled_black",
          size: "large",
          width: 300,
          text: "signin_with",
          shape: "pill",
        });
      }
    };
    document.head.appendChild(script);
    return () => { document.head.removeChild(script); };
  }, [handleCredentialResponse]);

  // No Google Client ID configured — fall back to password gate
  if (!GOOGLE_CLIENT_ID) {
    return <PasswordFallback onUnlock={onUnlock} />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-8 w-full max-w-sm text-center"
      >
        <h1
          className="text-3xl font-bold mb-2 text-ethereal"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Taleweaver
        </h1>
        <p className="text-starlight/50 text-sm mb-6">Sign in to continue</p>

        <div className="flex justify-center">
          {checking ? (
            <p className="text-starlight/60 text-sm">Signing in...</p>
          ) : (
            <div ref={buttonRef} />
          )}
        </div>

        {error && (
          <p className="text-red-400 text-sm mt-4">{error}</p>
        )}
      </motion.div>
    </div>
  );
}

/** Password fallback for local dev when GOOGLE_CLIENT_ID is not set */
function PasswordFallback({ onUnlock }: { onUnlock: () => void }) {
  const [password, setPassword] = useState("");
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) return;
    setChecking(true);
    setError("");
    setAuthToken(password.trim());
    const ok = await verifyToken(password.trim());
    if (ok) {
      onUnlock();
    } else {
      setAuthToken("");
      setError("Wrong password");
      setChecking(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-8 w-full max-w-sm text-center"
      >
        <h1
          className="text-3xl font-bold mb-2 text-ethereal"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Taleweaver
        </h1>
        <p className="text-starlight/50 text-sm mb-6">Enter password to continue</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            autoFocus
            className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-starlight placeholder-starlight/30 focus:outline-none focus:border-purple-400/50 focus:ring-1 focus:ring-purple-400/30 transition-colors"
          />
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={checking || !password.trim()}
            className="w-full py-3 rounded-xl font-semibold transition-all duration-300 bg-gradient-to-r from-purple-500 to-indigo-500 text-white hover:shadow-lg hover:shadow-purple-500/25 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {checking ? "Checking..." : "Enter"}
          </button>
        </form>
      </motion.div>
    </div>
  );
}
