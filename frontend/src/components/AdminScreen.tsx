import { Fragment, useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import type { AllowedEmail, StoryLogEntry, StoryDetail } from "../types";
import {
  fetchAllowedEmails,
  addAllowedEmail,
  removeAllowedEmail,
  fetchStories,
  fetchStory,
} from "../api/client";

interface AdminScreenProps {
  onBack: () => void;
}

type Tab = "emails" | "stories";

export default function AdminScreen({ onBack }: AdminScreenProps) {
  const [tab, setTab] = useState<Tab>("stories");

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2
          className="text-2xl font-bold text-ethereal"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Admin
        </h2>
        <button
          onClick={onBack}
          className="text-starlight/50 hover:text-starlight transition-colors text-sm"
        >
          &larr; Back to app
        </button>
      </div>

      <div className="flex gap-2 mb-6">
        {(["stories", "emails"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t
                ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                : "text-starlight/50 hover:text-starlight/80"
            }`}
          >
            {t === "emails" ? "Allowed Emails" : "Story Log"}
          </button>
        ))}
      </div>

      {tab === "emails" ? <EmailsTab /> : <StoriesTab />}
    </div>
  );
}

function EmailsTab() {
  const [emails, setEmails] = useState<AllowedEmail[]>([]);
  const [newEmail, setNewEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const data = await fetchAllowedEmails();
      setEmails(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load emails");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmail.trim()) return;
    setError("");
    try {
      await addAllowedEmail(newEmail.trim());
      setNewEmail("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add email");
    }
  };

  const handleRemove = async (email: string) => {
    setError("");
    try {
      await removeAllowedEmail(email);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove email");
    }
  };

  if (loading) return <p className="text-starlight/50">Loading...</p>;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      <form onSubmit={handleAdd} className="flex gap-2">
        <input
          type="email"
          value={newEmail}
          onChange={(e) => setNewEmail(e.target.value)}
          placeholder="user@gmail.com"
          className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-starlight placeholder-starlight/30 focus:outline-none focus:border-purple-400/50 text-sm"
        />
        <button
          type="submit"
          disabled={!newEmail.trim()}
          className="px-4 py-2 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-500/30 text-sm font-medium hover:bg-purple-500/30 disabled:opacity-50 transition-colors"
        >
          Add
        </button>
      </form>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <div className="glass-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left px-4 py-3 text-starlight/50 font-medium">Email</th>
              <th className="text-left px-4 py-3 text-starlight/50 font-medium">Added</th>
              <th className="px-4 py-3 w-16"></th>
            </tr>
          </thead>
          <tbody>
            {emails.map((e) => (
              <tr key={e.id} className="border-b border-white/5 hover:bg-white/5">
                <td className="px-4 py-3 text-starlight">{e.email}</td>
                <td className="px-4 py-3 text-starlight/50">
                  {new Date(e.added_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => handleRemove(e.email)}
                    className="text-red-400/60 hover:text-red-400 transition-colors text-xs"
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
            {emails.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-6 text-center text-starlight/30">
                  No emails in allowlist
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}

function StoriesTab() {
  const [stories, setStories] = useState<StoryLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);
  const [detail, setDetail] = useState<StoryDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const limit = 20;

  const load = useCallback(async (off: number) => {
    setLoading(true);
    try {
      const data = await fetchStories(limit, off);
      setStories(data.stories);
      setTotal(data.total);
      setOffset(off);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load stories");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(0); }, [load]);

  const handleExpand = async (id: number) => {
    if (expanded === id) {
      setExpanded(null);
      setDetail(null);
      return;
    }
    setExpanded(id);
    setDetailLoading(true);
    try {
      const d = await fetchStory(id);
      setDetail(d);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  if (loading && stories.length === 0) return <p className="text-starlight/50">Loading...</p>;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      {error && <p className="text-red-400 text-sm">{error}</p>}

      <p className="text-starlight/40 text-xs">{total} stories total</p>

      <div className="glass-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left px-3 py-3 text-starlight/50 font-medium">Date</th>
              <th className="text-left px-3 py-3 text-starlight/50 font-medium">User</th>
              <th className="text-left px-3 py-3 text-starlight/50 font-medium">Kid</th>
              <th className="text-left px-3 py-3 text-starlight/50 font-medium">Type</th>
              <th className="text-left px-3 py-3 text-starlight/50 font-medium">Title</th>
            </tr>
          </thead>
          <tbody>
            {stories.map((s) => (
              <Fragment key={s.id}>
                <tr
                  onClick={() => handleExpand(s.id)}
                  className="border-b border-white/5 hover:bg-white/5 cursor-pointer"
                >
                  <td className="px-3 py-3 text-starlight/60 whitespace-nowrap">
                    {new Date(s.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-3 py-3 text-starlight/60 truncate max-w-32">{s.user_email}</td>
                  <td className="px-3 py-3 text-starlight">
                    {s.kid_name}, {s.kid_age}
                  </td>
                  <td className="px-3 py-3 text-starlight/60">
                    {s.story_type === "custom" ? s.genre : s.event_id}
                  </td>
                  <td className="px-3 py-3 text-starlight truncate max-w-48">{s.title}</td>
                </tr>
                {expanded === s.id && (
                  <tr>
                    <td colSpan={5} className="px-3 py-4 bg-white/5">
                      {detailLoading ? (
                        <p className="text-starlight/50 text-sm">Loading...</p>
                      ) : detail ? (
                        <div className="space-y-4 text-sm">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <span className="text-starlight/40">Mood:</span>{" "}
                              <span className="text-starlight">{detail.mood || "\u2014"}</span>
                            </div>
                            <div>
                              <span className="text-starlight/40">Length:</span>{" "}
                              <span className="text-starlight">{detail.length || "\u2014"}</span>
                            </div>
                            <div>
                              <span className="text-starlight/40">Duration:</span>{" "}
                              <span className="text-starlight">{detail.duration_seconds}s</span>
                            </div>
                            <div>
                              <span className="text-starlight/40">Description:</span>{" "}
                              <span className="text-starlight">{detail.description || "\u2014"}</span>
                            </div>
                          </div>
                          <div>
                            <h4 className="text-starlight/40 mb-1">Prompt</h4>
                            <pre className="text-starlight/80 whitespace-pre-wrap bg-black/20 rounded-lg p-3 max-h-64 overflow-y-auto text-xs">
                              {detail.prompt}
                            </pre>
                          </div>
                          <div>
                            <h4 className="text-starlight/40 mb-1">Story</h4>
                            <pre className="text-starlight/80 whitespace-pre-wrap bg-black/20 rounded-lg p-3 max-h-64 overflow-y-auto text-xs">
                              {detail.story_text}
                            </pre>
                          </div>
                        </div>
                      ) : (
                        <p className="text-red-400 text-sm">Failed to load details</p>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
            {stories.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-starlight/30">
                  No stories generated yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {total > limit && (
        <div className="flex justify-center gap-2">
          <button
            disabled={offset === 0}
            onClick={() => load(Math.max(0, offset - limit))}
            className="px-3 py-1 rounded text-sm text-starlight/50 hover:text-starlight disabled:opacity-30 transition-colors"
          >
            &larr; Prev
          </button>
          <span className="text-starlight/40 text-sm py-1">
            {offset + 1}&ndash;{Math.min(offset + limit, total)} of {total}
          </span>
          <button
            disabled={offset + limit >= total}
            onClick={() => load(offset + limit)}
            className="px-3 py-1 rounded text-sm text-starlight/50 hover:text-starlight disabled:opacity-30 transition-colors"
          >
            Next &rarr;
          </button>
        </div>
      )}
    </motion.div>
  );
}
