import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { KidProfile, StoryMood, StoryLength, StoryType, WizardStep } from "./types";
import HeroScreen from "./components/HeroScreen";
import CraftScreen from "./components/CraftScreen";
import StoryScreen from "./components/StoryScreen";
import ParticleBackground from "./components/ParticleBackground";
import {
  createCustomStory,
  createHistoricalStory,
  pollJobStatus,
  getAudioUrl,
} from "./api/client";

const pageVariants = {
  initial: { opacity: 0, scale: 0.96 },
  animate: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: "easeOut" as const } },
  exit: { opacity: 0, scale: 1.04, transition: { duration: 0.3, ease: "easeIn" as const } },
};

const SESSION_KEY = "taleweaver_session";

interface SessionData {
  step: WizardStep;
  jobId?: string;
  kidProfile?: KidProfile | null;
  storyType?: StoryType;
  storyTitle?: string;
  storyDuration?: number;
  audioUrl?: string;
  isGenerating?: boolean;
  currentStage?: string;
}

function saveSession(data: SessionData) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(data));
  } catch { /* ignore */ }
}

function loadSession(): SessionData | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  return null;
}

function clearSession() {
  try { sessionStorage.removeItem(SESSION_KEY); } catch { /* ignore */ }
}

export default function App() {
  const saved = useRef(loadSession());

  const [step, setStep] = useState<WizardStep>(saved.current?.step ?? "hero");
  const [kidProfile, setKidProfile] = useState<KidProfile | null>(saved.current?.kidProfile ?? null);
  const [storyType, setStoryType] = useState<StoryType>(saved.current?.storyType ?? "custom");
  const [mood, setMood] = useState<StoryMood | undefined>();
  const [length, setLength] = useState<StoryLength | undefined>();
  const [currentStage, setCurrentStage] = useState(saved.current?.currentStage ?? "writing");
  const [storyTitle, setStoryTitle] = useState(saved.current?.storyTitle ?? "");
  const [storyDuration, setStoryDuration] = useState(saved.current?.storyDuration ?? 0);
  const [audioUrl, setAudioUrl] = useState(saved.current?.audioUrl ?? "");
  const [error, setError] = useState("");
  const [isGenerating, setIsGenerating] = useState(saved.current?.isGenerating ?? false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  const startPolling = useCallback((jobId: string) => {
    setIsGenerating(true);
    setCurrentStage("writing");

    pollingRef.current = setInterval(async () => {
      try {
        const status = await pollJobStatus(jobId);
        if (status.status === "complete" && "title" in status) {
          clearInterval(pollingRef.current);
          const url = getAudioUrl(jobId);
          setStoryTitle(status.title);
          setStoryDuration(status.duration_seconds);
          setAudioUrl(url);
          setIsGenerating(false);
          saveSession({ step: "story", storyTitle: status.title, storyDuration: status.duration_seconds, audioUrl: url, isGenerating: false });
        } else if (status.status === "failed") {
          clearInterval(pollingRef.current);
          setError("Something went wrong. Please try again.");
          setIsGenerating(false);
          clearSession();
        } else if ("current_stage" in status) {
          setCurrentStage(status.current_stage);
          saveSession({ step: "story", jobId, isGenerating: true, currentStage: status.current_stage });
        }
      } catch {
        clearInterval(pollingRef.current);
        setError("Connection lost. Please try again.");
        setIsGenerating(false);
        clearSession();
      }
    }, 2000);
  }, []);

  // Resume polling if we had an active job when the tab was suspended
  useEffect(() => {
    const s = saved.current;
    if (s?.step === "story" && s.isGenerating && s.jobId) {
      startPolling(s.jobId);
    }
    saved.current = null; // only run once
  }, [startPolling]);

  const handleCreateStory = async (genre: string, description: string) => {
    if (!kidProfile) return;
    setError("");
    setStep("story");
    try {
      const job = await createCustomStory(kidProfile, genre, description, mood, length);
      saveSession({ step: "story", jobId: job.job_id, kidProfile, storyType, isGenerating: true, currentStage: "writing" });
      startPolling(job.job_id);
    } catch {
      setError("Failed to create story. Please try again.");
      setStep("craft");
    }
  };

  const handleHistoricalStory = async (eventId: string) => {
    if (!kidProfile) return;
    setError("");
    setStep("story");
    try {
      const job = await createHistoricalStory(kidProfile, eventId, mood, length);
      saveSession({ step: "story", jobId: job.job_id, kidProfile, storyType, isGenerating: true, currentStage: "writing" });
      startPolling(job.job_id);
    } catch {
      setError("Failed to create story. Please try again.");
      setStep("craft");
    }
  };

  const handleCreateAnother = () => {
    setStep("craft");
    setStoryTitle("");
    setStoryDuration(0);
    setAudioUrl("");
    setError("");
    setIsGenerating(false);
    clearSession();
  };

  return (
    <div className="min-h-screen">
      <ParticleBackground />

      <div className="content-layer min-h-screen flex flex-col">
        <header className="py-8 text-center">
          <h1
            className="text-4xl md:text-5xl font-bold tracking-wide text-ethereal"
            style={{ fontFamily: "var(--font-display)", textShadow: "0 0 20px rgba(167, 139, 250, 0.5), 0 0 40px rgba(167, 139, 250, 0.2)" }}
          >
            Taleweaver
          </h1>
          <p className="text-starlight/40 mt-2 text-sm tracking-widest uppercase">
            Where stories come alive
          </p>
        </header>

        <main className="flex-1 px-4 pb-16">
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-lg mx-auto mb-6 p-4 glass-card text-red-300 text-center"
              style={{ borderColor: "rgba(239, 68, 68, 0.3)" }}
            >
              {error}
            </motion.div>
          )}

          <AnimatePresence mode="wait">
            {step === "hero" && (
              <motion.div key="hero" variants={pageVariants} initial="initial" animate="animate" exit="exit">
                <HeroScreen
                  onSubmit={(profile, type) => {
                    setKidProfile(profile);
                    setStoryType(type);
                    setStep("craft");
                  }}
                />
              </motion.div>
            )}

            {step === "craft" && (
              <motion.div key="craft" variants={pageVariants} initial="initial" animate="animate" exit="exit">
                <CraftScreen
                  storyType={storyType}
                  mood={mood}
                  length={length}
                  onMoodChange={setMood}
                  onLengthChange={setLength}
                  onSubmitCustom={handleCreateStory}
                  onSubmitHistorical={handleHistoricalStory}
                  onBack={() => setStep("hero")}
                  onTypeChange={setStoryType}
                />
              </motion.div>
            )}

            {step === "story" && (
              <motion.div key="story" variants={pageVariants} initial="initial" animate="animate" exit="exit">
                <StoryScreen
                  isGenerating={isGenerating}
                  currentStage={currentStage}
                  title={storyTitle}
                  audioUrl={audioUrl}
                  durationSeconds={storyDuration}
                  onCreateAnother={handleCreateAnother}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
