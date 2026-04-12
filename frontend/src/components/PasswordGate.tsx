import { useState } from "react";
import { motion } from "framer-motion";

interface PasswordGateProps {
  onUnlock: () => void;
  error?: string;
}

export default function PasswordGate({ onUnlock, error }: PasswordGateProps) {
  const [password, setPassword] = useState("");
  const [checking, setChecking] = useState(false);
  const [localError, setLocalError] = useState(error || "");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) return;
    setChecking(true);
    setLocalError("");

    const { verifyPassword, setStoredPassword } = await import("../api/client");
    const ok = await verifyPassword(password.trim());
    if (ok) {
      setStoredPassword(password.trim());
      onUnlock();
    } else {
      setLocalError("Wrong password");
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

          {localError && (
            <p className="text-red-400 text-sm">{localError}</p>
          )}

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
