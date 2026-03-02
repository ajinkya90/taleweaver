import { useCallback, useRef, useState } from "react";
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
  animate: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: "easeOut" } },
  exit: { opacity: 0, scale: 1.04, transition: { duration: 0.3, ease: "easeIn" } },
};

export default function App() {
  const [step, setStep] = useState<WizardStep>("hero");
  const [kidProfile, setKidProfile] = useState<KidProfile | null>(null);
  const [storyType, setStoryType] = useState<StoryType>("custom");
  const [mood, setMood] = useState<StoryMood | undefined>();
  const [length, setLength] = useState<StoryLength | undefined>();
  const [currentStage, setCurrentStage] = useState("writing");
  const [storyTitle, setStoryTitle] = useState("");
  const [storyDuration, setStoryDuration] = useState(0);
  const [audioUrl, setAudioUrl] = useState("");
  const [error, setError] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  const startPolling = useCallback((jobId: string) => {
    setIsGenerating(true);
    setCurrentStage("writing");

    pollingRef.current = setInterval(async () => {
      try {
        const status = await pollJobStatus(jobId);
        if (status.status === "complete" && "title" in status) {
          clearInterval(pollingRef.current);
          setStoryTitle(status.title);
          setStoryDuration(status.duration_seconds);
          setAudioUrl(getAudioUrl(jobId));
          setIsGenerating(false);
        } else if (status.status === "failed") {
          clearInterval(pollingRef.current);
          setError("Something went wrong. Please try again.");
          setIsGenerating(false);
        } else if ("current_stage" in status) {
          setCurrentStage(status.current_stage);
        }
      } catch {
        clearInterval(pollingRef.current);
        setError("Connection lost. Please try again.");
        setIsGenerating(false);
      }
    }, 2000);
  }, []);

  const handleCreateStory = async (genre: string, description: string) => {
    if (!kidProfile) return;
    setError("");
    setStep("story");
    const job = await createCustomStory(kidProfile, genre, description, mood, length);
    startPolling(job.job_id);
  };

  const handleHistoricalStory = async (eventId: string) => {
    if (!kidProfile) return;
    setError("");
    setStep("story");
    const job = await createHistoricalStory(kidProfile, eventId);
    startPolling(job.job_id);
  };

  const handleCreateAnother = () => {
    setStep("craft");
    setStoryTitle("");
    setStoryDuration(0);
    setAudioUrl("");
    setError("");
    setIsGenerating(false);
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
