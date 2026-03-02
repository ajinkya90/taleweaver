interface Props {
  currentStage: string;
}

const STAGE_LABELS: Record<string, string> = {
  writing: "Writing your story...",
  splitting: "Preparing character voices...",
  synthesizing: "Recording the narration...",
  stitching: "Finishing up...",
};

export default function GeneratingScreen({ currentStage }: Props) {
  const label = STAGE_LABELS[currentStage] || "Creating your story...";

  return (
    <div className="max-w-md mx-auto text-center space-y-8 py-12">
      <div className="text-6xl animate-bounce">📖</div>
      <h2 className="text-2xl font-bold text-purple-700">{label}</h2>
      <div className="flex justify-center gap-2">
        {Object.keys(STAGE_LABELS).map((stage) => (
          <div
            key={stage}
            className={`h-2 w-16 rounded-full transition-colors ${
              stage === currentStage
                ? "bg-purple-500 animate-pulse"
                : Object.keys(STAGE_LABELS).indexOf(stage) <
                  Object.keys(STAGE_LABELS).indexOf(currentStage)
                ? "bg-purple-300"
                : "bg-gray-200"
            }`}
          />
        ))}
      </div>
      <p className="text-gray-500 text-sm">This usually takes about a minute</p>
    </div>
  );
}
