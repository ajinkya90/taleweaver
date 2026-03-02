import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { KidProfile, StoryType } from "../types";

interface Props {
  onSubmit: (profile: KidProfile, type: StoryType) => void;
}

const PERSONALITIES = ["adventurous", "curious", "shy", "funny"];
const AGES = Array.from({ length: 10 }, (_, i) => i + 3); // 3–12

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.15 },
  },
};

const item = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 260, damping: 20 } },
};

export default function HeroScreen({ onSubmit }: Props) {
  const [name, setName] = useState("");
  const [age, setAge] = useState<number | null>(null);
  const [showPersonalize, setShowPersonalize] = useState(false);

  const [favoriteAnimal, setFavoriteAnimal] = useState("");
  const [favoriteColor, setFavoriteColor] = useState("");
  const [hobby, setHobby] = useState("");
  const [bestFriend, setBestFriend] = useState("");
  const [petName, setPetName] = useState("");
  const [personality, setPersonality] = useState("");

  const isValid = name.trim().length > 0 && age !== null;

  function buildProfile(): KidProfile {
    const profile: KidProfile = {
      name: name.trim(),
      age: age!,
    };
    if (favoriteAnimal.trim()) profile.favorite_animal = favoriteAnimal.trim();
    if (favoriteColor.trim()) profile.favorite_color = favoriteColor.trim();
    if (hobby.trim()) profile.hobby = hobby.trim();
    if (bestFriend.trim()) profile.best_friend = bestFriend.trim();
    if (petName.trim()) profile.pet_name = petName.trim();
    if (personality) profile.personality = personality;
    return profile;
  }

  function handleSubmit(type: StoryType) {
    if (!isValid) return;
    onSubmit(buildProfile(), type);
  }

  return (
    <motion.div
      className="w-full max-w-2xl mx-auto px-4 py-8"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* ---------- Title ---------- */}
      <motion.h1
        variants={item}
        className="font-display text-glow text-4xl sm:text-5xl text-center mb-10 text-starlight"
      >
        Who's the hero?
      </motion.h1>

      {/* ---------- Name input ---------- */}
      <motion.div variants={item} className="mb-6">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Your child's name"
          className="glow-input w-full text-lg"
        />
      </motion.div>

      {/* ---------- Age selector ---------- */}
      <motion.div variants={item} className="mb-8">
        <p className="text-starlight/60 text-sm mb-3 text-center">Age</p>
        <div className="flex flex-wrap justify-center gap-2">
          {AGES.map((a) => (
            <motion.button
              key={a}
              type="button"
              whileTap={{ scale: 0.85 }}
              whileHover={{ scale: 1.1 }}
              onClick={() => setAge(a)}
              className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-200 cursor-pointer ${
                age === a
                  ? "bg-mystic text-white shadow-[0_0_18px_rgba(124,58,237,0.6)]"
                  : "bg-white/5 text-starlight/70 hover:bg-white/10"
              }`}
            >
              {a}
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* ---------- Personalize toggle ---------- */}
      <motion.div variants={item} className="mb-8">
        <button
          type="button"
          onClick={() => setShowPersonalize((v) => !v)}
          className="mx-auto flex items-center gap-2 text-ethereal/80 hover:text-ethereal transition-colors text-sm cursor-pointer"
        >
          <motion.span
            animate={{ rotate: showPersonalize ? 90 : 0 }}
            transition={{ duration: 0.2 }}
            className="inline-block"
          >
            ▸
          </motion.span>
          Personalize the story
        </button>

        <AnimatePresence>
          {showPersonalize && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
                <input
                  type="text"
                  value={favoriteAnimal}
                  onChange={(e) => setFavoriteAnimal(e.target.value)}
                  placeholder="Favorite animal"
                  className="glow-input w-full"
                />
                <input
                  type="text"
                  value={favoriteColor}
                  onChange={(e) => setFavoriteColor(e.target.value)}
                  placeholder="Favorite color"
                  className="glow-input w-full"
                />
                <input
                  type="text"
                  value={hobby}
                  onChange={(e) => setHobby(e.target.value)}
                  placeholder="Hobby"
                  className="glow-input w-full"
                />
                <input
                  type="text"
                  value={bestFriend}
                  onChange={(e) => setBestFriend(e.target.value)}
                  placeholder="Best friend's name"
                  className="glow-input w-full"
                />
                <input
                  type="text"
                  value={petName}
                  onChange={(e) => setPetName(e.target.value)}
                  placeholder="Pet's name"
                  className="glow-input w-full"
                />

                {/* Personality pills */}
                <div className="flex flex-wrap items-center gap-2 sm:col-span-2">
                  <span className="text-starlight/50 text-sm mr-1">Personality:</span>
                  {PERSONALITIES.map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setPersonality(personality === p ? "" : p)}
                      className={`px-3 py-1 rounded-full text-xs font-medium capitalize transition-all cursor-pointer ${
                        personality === p
                          ? "bg-mystic text-white shadow-[0_0_12px_rgba(124,58,237,0.5)]"
                          : "bg-white/5 text-starlight/60 hover:bg-white/10"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* ---------- Story type cards ---------- */}
      <motion.div variants={item}>
        <p className="text-starlight/50 text-sm text-center mb-4">
          Choose your adventure
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Custom Story */}
          <motion.button
            type="button"
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            disabled={!isValid}
            onClick={() => handleSubmit("custom")}
            className="glass-card p-6 text-left transition-shadow duration-300 hover:shadow-[0_0_30px_rgba(124,58,237,0.25)] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            <span className="text-3xl mb-3 block">✨</span>
            <h3 className="font-display text-lg text-starlight mb-1">
              Custom Story
            </h3>
            <p className="text-starlight/50 text-sm">
              Create your own adventure
            </p>
          </motion.button>

          {/* Historical Adventure */}
          <motion.button
            type="button"
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            disabled={!isValid}
            onClick={() => handleSubmit("historical")}
            className="glass-card p-6 text-left transition-shadow duration-300 hover:shadow-[0_0_30px_rgba(124,58,237,0.25)] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            <span className="text-3xl mb-3 block">🏛️</span>
            <h3 className="font-display text-lg text-starlight mb-1">
              Historical Adventure
            </h3>
            <p className="text-starlight/50 text-sm">
              Travel through time
            </p>
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
}
