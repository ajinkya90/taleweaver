import { useCallback, useRef, useState } from "react";
import type { KidProfile, WizardStep } from "./types";
import KidProfileForm from "./components/KidProfileForm";
import StoryTypeSelector from "./components/StoryTypeSelector";
import CustomStoryForm from "./components/CustomStoryForm";
import HistoricalEventPicker from "./components/HistoricalEventPicker";
import GeneratingScreen from "./components/GeneratingScreen";
import AudioPlayer from "./components/AudioPlayer";
import {
  createCustomStory,
  createHistoricalStory,
  pollJobStatus,
  getAudioUrl,
} from "./api/client";

export default function App() {
  const [step, setStep] = useState<WizardStep>("profile");
  const [kidProfile, setKidProfile] = useState<KidProfile | null>(null);
  const [currentStage, setCurrentStage] = useState("writing");
  const [storyTitle, setStoryTitle] = useState("");
  const [storyDuration, setStoryDuration] = useState(0);
  const [audioUrl, setAudioUrl] = useState("");
  const [error, setError] = useState("");
  const pollingRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  const startPolling = useCallback((jobId: string) => {
    setStep("generating");
    setCurrentStage("writing");

    pollingRef.current = setInterval(async () => {
      try {
        const status = await pollJobStatus(jobId);
        if (status.status === "complete" && "title" in status) {
          clearInterval(pollingRef.current);
          setStoryTitle(status.title);
          setStoryDuration(status.duration_seconds);
          setAudioUrl(getAudioUrl(jobId));
          setStep("listen");
        } else if (status.status === "failed") {
          clearInterval(pollingRef.current);
          setError("Something went wrong. Please try again.");
          setStep("story-type");
        } else if ("current_stage" in status) {
          setCurrentStage(status.current_stage);
        }
      } catch {
        clearInterval(pollingRef.current);
        setError("Connection lost. Please try again.");
        setStep("story-type");
      }
    }, 2000);
  }, []);

  const handleCustomStory = async (genre: string, description: string) => {
    if (!kidProfile) return;
    setError("");
    const job = await createCustomStory(kidProfile, genre, description);
    startPolling(job.job_id);
  };

  const handleHistoricalStory = async (eventId: string) => {
    if (!kidProfile) return;
    setError("");
    const job = await createHistoricalStory(kidProfile, eventId);
    startPolling(job.job_id);
  };

  const handleCreateAnother = () => {
    setStep("story-type");
    setStoryTitle("");
    setStoryDuration(0);
    setAudioUrl("");
    setError("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white">
      <header className="py-8 text-center">
        <h1 className="text-4xl font-extrabold text-purple-800">
          StoryForge
        </h1>
        <p className="text-gray-500 mt-1">Magical audio stories for kids</p>
      </header>

      <main className="px-4 pb-16">
        {error && (
          <div className="max-w-lg mx-auto mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-center">
            {error}
          </div>
        )}

        {step === "profile" && (
          <KidProfileForm
            onSubmit={(profile) => {
              setKidProfile(profile);
              setStep("story-type");
            }}
          />
        )}

        {step === "story-type" && (
          <StoryTypeSelector
            onSelect={(type) =>
              setStep(type === "custom" ? "custom-form" : "historical-pick")
            }
          />
        )}

        {step === "custom-form" && (
          <CustomStoryForm
            onSubmit={handleCustomStory}
            onBack={() => setStep("story-type")}
          />
        )}

        {step === "historical-pick" && (
          <HistoricalEventPicker
            onSelect={handleHistoricalStory}
            onBack={() => setStep("story-type")}
          />
        )}

        {step === "generating" && (
          <GeneratingScreen currentStage={currentStage} />
        )}

        {step === "listen" && (
          <AudioPlayer
            title={storyTitle}
            audioUrl={audioUrl}
            durationSeconds={storyDuration}
            onCreateAnother={handleCreateAnother}
          />
        )}
      </main>
    </div>
  );
}
