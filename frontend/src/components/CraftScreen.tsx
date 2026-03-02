import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import type {
  StoryType,
  StoryMood,
  StoryLength,
  Genre,
  HistoricalEvent,
} from "../types";
import { fetchGenres, fetchHistoricalEvents } from "../api/client";

interface Props {
  storyType: StoryType;
  mood?: StoryMood;
  length?: StoryLength;
  onMoodChange: (mood: StoryMood | undefined) => void;
  onLengthChange: (length: StoryLength | undefined) => void;
  onSubmitCustom: (genre: string, description: string) => void;
  onSubmitHistorical: (eventId: string) => void;
  onBack: () => void;
  onTypeChange: (type: StoryType) => void;
}

const MOODS: { value: StoryMood; emoji: string; label: string }[] = [
  { value: "exciting", emoji: "\u26A1", label: "Exciting" },
  { value: "heartwarming", emoji: "\uD83D\uDC9B", label: "Heartwarming" },
  { value: "funny", emoji: "\uD83D\uDE04", label: "Funny" },
  { value: "mysterious", emoji: "\uD83D\uDD2E", label: "Mysterious" },
];

const LENGTHS: { value: StoryLength; label: string }[] = [
  { value: "short", label: "Short" },
  { value: "medium", label: "Medium" },
  { value: "long", label: "Long" },
];

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.06 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } },
};

function formatYear(year: number): string {
  if (year < 0) return `${Math.abs(year)} BCE`;
  return String(year);
}

export default function CraftScreen({
  storyType,
  mood,
  length,
  onMoodChange,
  onLengthChange,
  onSubmitCustom,
  onSubmitHistorical,
  onBack,
  onTypeChange,
}: Props) {
  const [genres, setGenres] = useState<Genre[]>([]);
  const [events, setEvents] = useState<HistoricalEvent[]>([]);
  const [selectedGenre, setSelectedGenre] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => {
    fetchGenres().then(setGenres);
    fetchHistoricalEvents().then(setEvents);
  }, []);

  const canSubmitCustom = selectedGenre !== "" && description.trim() !== "";

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (canSubmitCustom) {
      onSubmitCustom(selectedGenre, description.trim());
    }
  };

  return (
    <motion.div
      className="max-w-3xl mx-auto px-4 py-8"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Title */}
      <motion.h1
        className="text-3xl md:text-4xl font-bold text-center text-glow mb-8"
        style={{ fontFamily: "var(--font-display)" }}
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        Craft the Adventure
      </motion.h1>

      {/* Type toggle */}
      <motion.div
        className="flex justify-center gap-2 mb-10"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
      >
        <button
          onClick={() => onTypeChange("custom")}
          className={`px-6 py-2 rounded-full font-semibold text-sm transition-all duration-300 ${
            storyType === "custom"
              ? "bg-[var(--color-mystic)] text-white shadow-[0_0_20px_rgba(124,58,237,0.5)]"
              : "glass-card text-[var(--color-ethereal)] hover:text-white"
          }`}
        >
          Custom Story
        </button>
        <button
          onClick={() => onTypeChange("historical")}
          className={`px-6 py-2 rounded-full font-semibold text-sm transition-all duration-300 ${
            storyType === "historical"
              ? "bg-[var(--color-mystic)] text-white shadow-[0_0_20px_rgba(124,58,237,0.5)]"
              : "glass-card text-[var(--color-ethereal)] hover:text-white"
          }`}
        >
          Historical Adventure
        </button>
      </motion.div>

      {/* Custom Story Path */}
      {storyType === "custom" && (
        <motion.form
          key="custom"
          onSubmit={handleCustomSubmit}
          className="space-y-8"
          initial="hidden"
          animate="visible"
          variants={containerVariants}
        >
          {/* Genre cards */}
          <motion.div variants={itemVariants}>
            <h2 className="text-lg font-semibold text-[var(--color-ethereal)] mb-3">
              Choose a Genre
            </h2>
            <motion.div
              className="grid grid-cols-2 md:grid-cols-3 gap-3"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              {genres.map((genre) => (
                <motion.button
                  key={genre.id}
                  type="button"
                  variants={itemVariants}
                  whileHover={{ scale: 1.04, boxShadow: "0 0 20px rgba(124,58,237,0.3)" }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() =>
                    setSelectedGenre(selectedGenre === genre.id ? "" : genre.id)
                  }
                  className={`glass-card p-4 text-left transition-all duration-300 cursor-pointer ${
                    selectedGenre === genre.id
                      ? "border-[var(--color-mystic)] shadow-[0_0_20px_rgba(124,58,237,0.4)] !border-[var(--color-mystic)]"
                      : ""
                  }`}
                  style={
                    selectedGenre === genre.id
                      ? { borderColor: "var(--color-mystic)", boxShadow: "0 0 20px rgba(124,58,237,0.4)" }
                      : {}
                  }
                >
                  <div className="text-2xl mb-1">{genre.icon}</div>
                  <div className="font-semibold text-[var(--color-starlight)] text-sm">
                    {genre.name}
                  </div>
                  <div className="text-xs text-[var(--color-ethereal)] opacity-60 mt-1">
                    {genre.description}
                  </div>
                </motion.button>
              ))}
            </motion.div>
          </motion.div>

          {/* Description textarea */}
          <motion.div variants={itemVariants}>
            <h2 className="text-lg font-semibold text-[var(--color-ethereal)] mb-3">
              Describe Your Story Idea
            </h2>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="glow-input w-full resize-none"
              placeholder="Describe your story idea..."
            />
          </motion.div>

          {/* Mood selector */}
          <motion.div variants={itemVariants}>
            <h2 className="text-lg font-semibold text-[var(--color-ethereal)] mb-3">
              Mood
              <span className="text-xs font-normal text-[var(--color-ethereal)] opacity-40 ml-2">
                optional
              </span>
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {MOODS.map((m) => (
                <motion.button
                  key={m.value}
                  type="button"
                  whileHover={{ scale: 1.04, boxShadow: "0 0 15px rgba(124,58,237,0.25)" }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() =>
                    onMoodChange(mood === m.value ? undefined : m.value)
                  }
                  className={`glass-card px-3 py-3 text-center text-sm font-medium transition-all duration-300 cursor-pointer ${
                    mood === m.value ? "" : ""
                  }`}
                  style={
                    mood === m.value
                      ? { borderColor: "var(--color-mystic)", boxShadow: "0 0 18px rgba(124,58,237,0.4)" }
                      : {}
                  }
                >
                  <span className="text-lg">{m.emoji}</span>
                  <div className="text-[var(--color-starlight)] mt-1">{m.label}</div>
                </motion.button>
              ))}
            </div>
          </motion.div>

          {/* Length selector */}
          <motion.div variants={itemVariants}>
            <h2 className="text-lg font-semibold text-[var(--color-ethereal)] mb-3">
              Length
              <span className="text-xs font-normal text-[var(--color-ethereal)] opacity-40 ml-2">
                optional
              </span>
            </h2>
            <div className="flex gap-3">
              {LENGTHS.map((l) => (
                <button
                  key={l.value}
                  type="button"
                  onClick={() =>
                    onLengthChange(length === l.value ? undefined : l.value)
                  }
                  className={`px-5 py-2 rounded-full text-sm font-semibold transition-all duration-300 ${
                    length === l.value
                      ? "bg-[var(--color-mystic)] text-white shadow-[0_0_15px_rgba(124,58,237,0.4)]"
                      : "glass-card text-[var(--color-ethereal)] hover:text-white cursor-pointer"
                  }`}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </motion.div>

          {/* Actions */}
          <motion.div
            className="flex items-center justify-between pt-4"
            variants={itemVariants}
          >
            <button
              type="button"
              onClick={onBack}
              className="px-5 py-2.5 rounded-xl border border-[var(--color-glass-border)] text-[var(--color-ethereal)] text-sm font-medium hover:border-[var(--color-ethereal)] hover:text-white transition-all duration-300 cursor-pointer"
            >
              &larr; Back
            </button>
            <button
              type="submit"
              disabled={!canSubmitCustom}
              className="btn-glow text-sm cursor-pointer"
            >
              Create Story
            </button>
          </motion.div>
        </motion.form>
      )}

      {/* Historical Path */}
      {storyType === "historical" && (
        <motion.div
          key="historical"
          className="space-y-6"
          initial="hidden"
          animate="visible"
          variants={containerVariants}
        >
          <motion.div
            className="grid grid-cols-1 md:grid-cols-2 gap-4"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {events.map((event) => (
              <motion.button
                key={event.id}
                variants={itemVariants}
                whileHover={{ scale: 1.03, boxShadow: "0 0 25px rgba(124,58,237,0.3)" }}
                whileTap={{ scale: 0.97 }}
                onClick={() => onSubmitHistorical(event.id)}
                className="glass-card p-5 text-left transition-all duration-300 cursor-pointer"
              >
                <div className="flex justify-between items-start gap-2">
                  <h3 className="font-bold text-[var(--color-starlight)] text-base">
                    {event.title}
                  </h3>
                  <span className="text-xs font-mono text-[var(--color-gold)] whitespace-nowrap">
                    {formatYear(event.year)}
                  </span>
                </div>
                <p className="text-sm text-[var(--color-ethereal)] mt-1 font-medium">
                  {event.figure}
                </p>
                <p className="text-xs text-[var(--color-ethereal)] opacity-50 mt-2 leading-relaxed">
                  {event.summary}
                </p>
              </motion.button>
            ))}
          </motion.div>

          {/* Back button */}
          <motion.div variants={itemVariants}>
            <button
              onClick={onBack}
              className="px-5 py-2.5 rounded-xl border border-[var(--color-glass-border)] text-[var(--color-ethereal)] text-sm font-medium hover:border-[var(--color-ethereal)] hover:text-white transition-all duration-300 cursor-pointer"
            >
              &larr; Back
            </button>
          </motion.div>
        </motion.div>
      )}
    </motion.div>
  );
}
