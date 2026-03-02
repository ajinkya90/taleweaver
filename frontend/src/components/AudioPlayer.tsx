import { useRef, useState } from "react";

interface Props {
  title: string;
  audioUrl: string;
  durationSeconds: number;
  onCreateAnother: () => void;
}

export default function AudioPlayer({
  title,
  audioUrl,
  durationSeconds,
  onCreateAnother,
}: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="max-w-lg mx-auto text-center space-y-6">
      <div className="text-5xl">🎧</div>
      <h2 className="text-2xl font-bold text-purple-700">{title}</h2>

      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={() =>
          setCurrentTime(audioRef.current?.currentTime || 0)
        }
        onEnded={() => setIsPlaying(false)}
      />

      <div className="bg-purple-50 rounded-2xl p-6 space-y-4">
        <input
          type="range"
          min={0}
          max={durationSeconds}
          value={currentTime}
          onChange={(e) => {
            const t = Number(e.target.value);
            if (audioRef.current) audioRef.current.currentTime = t;
            setCurrentTime(t);
          }}
          className="w-full accent-purple-600"
        />
        <div className="flex justify-between text-sm text-gray-500">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(durationSeconds)}</span>
        </div>
        <button
          onClick={togglePlay}
          className="w-16 h-16 bg-purple-600 text-white rounded-full text-2xl hover:bg-purple-700 transition-colors mx-auto flex items-center justify-center"
        >
          {isPlaying ? "⏸" : "▶"}
        </button>
      </div>

      <div className="flex gap-4 justify-center">
        <a
          href={audioUrl}
          download
          className="px-6 py-3 border-2 border-purple-300 rounded-xl hover:bg-purple-50 transition-colors font-medium"
        >
          Download MP3
        </a>
        <button
          onClick={onCreateAnother}
          className="px-6 py-3 bg-purple-600 text-white font-bold rounded-xl hover:bg-purple-700 transition-colors"
        >
          Create Another Story
        </button>
      </div>
    </div>
  );
}
