import { useRef, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

const STAGE_LABELS: Record<string, string> = {
  writing: "Writing the story...",
  splitting: "Preparing character voices...",
  synthesizing: "Generating audio...",
  stitching: "Mixing the final track...",
};

interface Props {
  isGenerating: boolean;
  currentStage?: string;
  title: string;
  audioUrl: string;
  durationSeconds: number;
  onCreateAnother: () => void;
}

const formatTime = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
};

export default function StoryScreen({
  isGenerating,
  currentStage,
  title,
  audioUrl,
  durationSeconds,
  onCreateAnother,
}: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(durationSeconds);
  const [isSeeking, setIsSeeking] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);

  // Sync duration from props when they change
  useEffect(() => {
    setDuration(durationSeconds);
  }, [durationSeconds]);

  const handleLoadedMetadata = () => {
    if (audioRef.current && audioRef.current.duration && isFinite(audioRef.current.duration)) {
      setDuration(audioRef.current.duration);
    }
  };

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch((err) => {
        console.error("Playback failed:", err);
        setIsPlaying(false);
      });
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const t = Number(e.target.value);
    if (audioRef.current) audioRef.current.currentTime = t;
    setCurrentTime(t);
  };

  const handleSeekStart = () => setIsSeeking(true);
  const handleSeekEnd = () => setIsSeeking(false);

  const handleTimeUpdate = () => {
    if (!isSeeking && audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleAudioError = () => {
    setAudioError("Failed to load audio. Please try again.");
    setIsPlaying(false);
  };

  // Build download URL with ?download=true
  const downloadUrl = audioUrl ? `${audioUrl}?download=true` : "";

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
      <AnimatePresence mode="wait">
        {isGenerating ? (
          /* ─── Phase 1: Generation Animation ─── */
          <motion.div
            key="generating"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.5 }}
            className="flex flex-col items-center space-y-8"
          >
            {/* Color-Cycling Pulsing Orb */}
            <motion.div
              className="w-32 h-32 rounded-full orb-color-cycle"
              animate={{
                scale: [1, 1.15, 1],
                opacity: [0.8, 1, 0.8],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
            <style>{`
              @keyframes orbColorCycle {
                0%   { background: radial-gradient(circle, #a78bfa 0%, #7c3aed 50%, #4c1d95 100%);
                       box-shadow: 0 0 40px rgba(124,58,237,0.6), 0 0 80px rgba(124,58,237,0.3); }
                25%  { background: radial-gradient(circle, #93c5fd 0%, #3b82f6 50%, #1e3a8a 100%);
                       box-shadow: 0 0 40px rgba(59,130,246,0.6), 0 0 80px rgba(59,130,246,0.3); }
                50%  { background: radial-gradient(circle, #6ee7b7 0%, #10b981 50%, #064e3b 100%);
                       box-shadow: 0 0 40px rgba(16,185,129,0.6), 0 0 80px rgba(16,185,129,0.3); }
                75%  { background: radial-gradient(circle, #fda4af 0%, #e11d48 50%, #881337 100%);
                       box-shadow: 0 0 40px rgba(225,29,72,0.6), 0 0 80px rgba(225,29,72,0.3); }
                100% { background: radial-gradient(circle, #a78bfa 0%, #7c3aed 50%, #4c1d95 100%);
                       box-shadow: 0 0 40px rgba(124,58,237,0.6), 0 0 80px rgba(124,58,237,0.3); }
              }
              .orb-color-cycle {
                animation: orbColorCycle 8s ease-in-out infinite;
              }
            `}</style>

            {/* Stage Label */}
            <p className="text-xl font-display text-glow text-ethereal">
              {currentStage ? (STAGE_LABELS[currentStage] ?? "Creating your story...") : "Creating your story..."}
            </p>

            {/* Subtitle */}
            <p className="text-sm text-starlight/40">
              This usually takes about a minute
            </p>
          </motion.div>
        ) : (
          audioUrl && (
            /* ─── Phase 2: Audio Player ─── */
            <motion.div
              key="player"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, ease: "easeOut" }}
              className="flex flex-col items-center space-y-8 w-full max-w-md"
            >
              {/* Story Title */}
              <h2 className="text-3xl md:text-4xl font-display text-glow text-center leading-snug">
                {title}
              </h2>

              {/* Player Card */}
              <div className="glass-card w-full p-6 space-y-6">
                {audioError ? (
                  <p className="text-red-400 text-center text-sm">{audioError}</p>
                ) : (
                  <>
                    {/* Seek Bar */}
                    <input
                      type="range"
                      min={0}
                      max={duration || 1}
                      step={0.1}
                      value={currentTime}
                      onChange={handleSeek}
                      onMouseDown={handleSeekStart}
                      onMouseUp={handleSeekEnd}
                      onTouchStart={handleSeekStart}
                      onTouchEnd={handleSeekEnd}
                      className="w-full h-2 rounded-full appearance-none cursor-pointer
                        bg-white/10
                        [&::-webkit-slider-thumb]:appearance-none
                        [&::-webkit-slider-thumb]:w-4
                        [&::-webkit-slider-thumb]:h-4
                        [&::-webkit-slider-thumb]:rounded-full
                        [&::-webkit-slider-thumb]:bg-mystic
                        [&::-webkit-slider-thumb]:shadow-[0_0_10px_rgba(124,58,237,0.6)]
                        [&::-webkit-slider-runnable-track]:rounded-full
                        [&::-moz-range-thumb]:w-4
                        [&::-moz-range-thumb]:h-4
                        [&::-moz-range-thumb]:rounded-full
                        [&::-moz-range-thumb]:bg-mystic
                        [&::-moz-range-thumb]:border-none
                        [&::-moz-range-thumb]:shadow-[0_0_10px_rgba(124,58,237,0.6)]
                        accent-mystic"
                    />

                    {/* Time Display */}
                    <div className="flex justify-between text-sm text-starlight/40">
                      <span>{formatTime(currentTime)}</span>
                      <span>{formatTime(duration)}</span>
                    </div>

                    {/* Play/Pause Button */}
                    <div className="flex justify-center">
                      <motion.button
                        onClick={togglePlay}
                        whileTap={{ scale: 0.9 }}
                        whileHover={{
                          boxShadow:
                            "0 0 30px rgba(124, 58, 237, 0.6), 0 0 60px rgba(124, 58, 237, 0.3)",
                        }}
                        className="w-20 h-20 rounded-full flex items-center justify-center text-3xl text-white cursor-pointer"
                        style={{
                          background:
                            "linear-gradient(135deg, #7c3aed, #6d28d9)",
                          boxShadow:
                            "0 0 20px rgba(124, 58, 237, 0.4), 0 0 40px rgba(124, 58, 237, 0.15)",
                        }}
                      >
                        {isPlaying ? "⏸" : "▶"}
                      </motion.button>
                    </div>
                  </>
                )}

                {/* Hidden Audio Element */}
                <audio
                  ref={audioRef}
                  src={audioUrl}
                  preload="auto"
                  onLoadedMetadata={handleLoadedMetadata}
                  onTimeUpdate={handleTimeUpdate}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onEnded={() => setIsPlaying(false)}
                  onError={handleAudioError}
                />
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 w-full">
                <a
                  href={downloadUrl}
                  download
                  className="glass-card px-6 py-3 text-center font-semibold text-starlight transition-all hover:text-glow"
                >
                  Download MP3
                </a>
                <button
                  onClick={onCreateAnother}
                  className="btn-glow flex-1 text-center"
                >
                  Create Another Story
                </button>
              </div>
            </motion.div>
          )
        )}
      </AnimatePresence>
    </div>
  );
}
