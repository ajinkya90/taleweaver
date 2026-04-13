import { Fragment, useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import type { MyStoryEntry, MyStoryDetail } from "../types";
import {
  fetchMyStories,
  fetchMyStory,
  getMyStoryAudioUrl,
} from "../api/client";

interface MyStoriesScreenProps {
  onBack: () => void;
}

export default function MyStoriesScreen({ onBack }: MyStoriesScreenProps) {
  const [stories, setStories] = useState<MyStoryEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);
  const [detail, setDetail] = useState<MyStoryDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const limit = 20;

  const load = useCallback(async (off: number) => {
    setLoading(true);
    try {
      const data = await fetchMyStories(limit, off);
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
      const d = await fetchMyStory(id);
      setDetail(d);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  if (loading && stories.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 text-center">
        <p className="text-starlight/50">Loading your stories...</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h2
          className="text-2xl font-bold text-ethereal"
          style={{ fontFamily: "var(--font-display)" }}
        >
          My Stories
        </h2>
        <button
          onClick={onBack}
          className="text-starlight/50 hover:text-starlight transition-colors text-sm"
        >
          &larr; Create new story
        </button>
      </div>

      {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

      {stories.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass-card p-12 text-center"
        >
          <p className="text-starlight/40 text-lg mb-2">No stories yet</p>
          <p className="text-starlight/30 text-sm">
            Create your first story and it will appear here
          </p>
        </motion.div>
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
          {stories.map((s) => (
            <Fragment key={s.id}>
              <motion.div
                onClick={() => handleExpand(s.id)}
                className={`glass-card p-4 cursor-pointer transition-all duration-300 hover:shadow-[0_0_20px_rgba(124,58,237,0.2)] ${
                  expanded === s.id ? "border-purple-500/30" : ""
                }`}
                style={expanded === s.id ? { borderColor: "rgba(124,58,237,0.3)" } : {}}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-starlight font-semibold truncate">{s.title}</h3>
                    <p className="text-starlight/40 text-sm mt-1">
                      {s.kid_name}, age {s.kid_age}
                      <span className="mx-2">-</span>
                      {s.story_type === "custom" ? s.genre : s.event_id}
                    </p>
                  </div>
                  <div className="text-right ml-4 flex-shrink-0">
                    <p className="text-starlight/50 text-xs">
                      {new Date(s.created_at).toLocaleDateString()}
                    </p>
                    <p className="text-starlight/30 text-xs mt-1">
                      {Math.floor(s.duration_seconds / 60)}:{String(s.duration_seconds % 60).padStart(2, "0")}
                    </p>
                  </div>
                </div>
              </motion.div>

              {expanded === s.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="glass-card p-5 space-y-4"
                >
                  {detailLoading ? (
                    <p className="text-starlight/50 text-sm">Loading...</p>
                  ) : detail ? (
                    <>
                      {/* Audio player */}
                      <div>
                        <audio
                          controls
                          src={getMyStoryAudioUrl(s.id)}
                          className="w-full"
                          preload="none"
                        />
                      </div>

                      {/* Metadata */}
                      <div className="flex flex-wrap gap-3 text-xs text-starlight/40">
                        {detail.mood && <span>Mood: {detail.mood}</span>}
                        {detail.length && <span>Length: {detail.length}</span>}
                        <span>Duration: {detail.duration_seconds}s</span>
                      </div>

                      {/* Transcript */}
                      <div>
                        <h4 className="text-starlight/40 text-sm mb-2">Story</h4>
                        <pre className="text-starlight/80 whitespace-pre-wrap bg-black/20 rounded-lg p-4 max-h-80 overflow-y-auto text-sm leading-relaxed">
                          {detail.story_text}
                        </pre>
                      </div>
                    </>
                  ) : (
                    <p className="text-red-400 text-sm">Failed to load story details</p>
                  )}
                </motion.div>
              )}
            </Fragment>
          ))}

          {total > limit && (
            <div className="flex justify-center gap-2 pt-4">
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
      )}
    </div>
  );
}
