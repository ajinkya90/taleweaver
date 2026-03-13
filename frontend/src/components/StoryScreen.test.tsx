import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import StoryScreen from './StoryScreen';

describe('StoryScreen - generating state', () => {
  it('shows writing stage label', () => {
    render(
      <StoryScreen
        isGenerating={true}
        currentStage="writing"
        title=""
        audioUrl=""
        durationSeconds={0}
        onCreateAnother={vi.fn()}
      />
    );
    expect(screen.getByText('Writing the story...')).toBeInTheDocument();
    expect(screen.getByText('This usually takes about a minute')).toBeInTheDocument();
  });

  it('shows splitting stage label', () => {
    render(
      <StoryScreen
        isGenerating={true}
        currentStage="splitting"
        title=""
        audioUrl=""
        durationSeconds={0}
        onCreateAnother={vi.fn()}
      />
    );
    expect(screen.getByText('Preparing character voices...')).toBeInTheDocument();
  });

  it('shows synthesizing stage label', () => {
    render(
      <StoryScreen
        isGenerating={true}
        currentStage="synthesizing"
        title=""
        audioUrl=""
        durationSeconds={0}
        onCreateAnother={vi.fn()}
      />
    );
    expect(screen.getByText('Generating audio...')).toBeInTheDocument();
  });

  it('shows stitching stage label', () => {
    render(
      <StoryScreen
        isGenerating={true}
        currentStage="stitching"
        title=""
        audioUrl=""
        durationSeconds={0}
        onCreateAnother={vi.fn()}
      />
    );
    expect(screen.getByText('Mixing the final track...')).toBeInTheDocument();
  });

  it('shows default label for unknown stage', () => {
    render(
      <StoryScreen
        isGenerating={true}
        currentStage="unknown"
        title=""
        audioUrl=""
        durationSeconds={0}
        onCreateAnother={vi.fn()}
      />
    );
    expect(screen.getByText('Creating your story...')).toBeInTheDocument();
  });

  it('shows default label when no stage provided', () => {
    render(
      <StoryScreen
        isGenerating={true}
        title=""
        audioUrl=""
        durationSeconds={0}
        onCreateAnother={vi.fn()}
      />
    );
    expect(screen.getByText('Creating your story...')).toBeInTheDocument();
  });
});

describe('StoryScreen - audio player', () => {
  it('shows title and player when generation completes', () => {
    render(
      <StoryScreen
        isGenerating={false}
        title="A Magical Journey"
        audioUrl="/api/story/audio/123"
        durationSeconds={120}
        onCreateAnother={vi.fn()}
      />
    );
    expect(screen.getByText('A Magical Journey')).toBeInTheDocument();
    expect(screen.getByText('Download MP3')).toBeInTheDocument();
    expect(screen.getByText('Create Another Story')).toBeInTheDocument();
  });

  it('download link has correct URL with download param', () => {
    render(
      <StoryScreen
        isGenerating={false}
        title="Test"
        audioUrl="/api/story/audio/123"
        durationSeconds={60}
        onCreateAnother={vi.fn()}
      />
    );
    const downloadLink = screen.getByText('Download MP3').closest('a');
    expect(downloadLink).toHaveAttribute('href', '/api/story/audio/123?download=true');
  });

  it('calls onCreateAnother when button clicked', () => {
    const onCreateAnother = vi.fn();
    render(
      <StoryScreen
        isGenerating={false}
        title="Test"
        audioUrl="/api/story/audio/123"
        durationSeconds={60}
        onCreateAnother={onCreateAnother}
      />
    );
    screen.getByText('Create Another Story').click();
    expect(onCreateAnother).toHaveBeenCalled();
  });

  it('shows play button initially', () => {
    render(
      <StoryScreen
        isGenerating={false}
        title="Test"
        audioUrl="/api/story/audio/123"
        durationSeconds={60}
        onCreateAnother={vi.fn()}
      />
    );
    // Play button should be visible (▶ character)
    const playBtn = screen.getByRole('button', { name: /▶/ });
    expect(playBtn).toBeInTheDocument();
  });

  it('formats time correctly', () => {
    render(
      <StoryScreen
        isGenerating={false}
        title="Test"
        audioUrl="/api/story/audio/123"
        durationSeconds={125}
        onCreateAnother={vi.fn()}
      />
    );
    // Should show 0:00 for current time and 2:05 for duration
    expect(screen.getByText('0:00')).toBeInTheDocument();
    expect(screen.getByText('2:05')).toBeInTheDocument();
  });

  it('has a range input for seeking', () => {
    render(
      <StoryScreen
        isGenerating={false}
        title="Test"
        audioUrl="/api/story/audio/123"
        durationSeconds={60}
        onCreateAnother={vi.fn()}
      />
    );
    const slider = screen.getByRole('slider');
    expect(slider).toBeInTheDocument();
    expect(slider).toHaveAttribute('min', '0');
  });

  it('shows nothing when not generating and no audio URL', () => {
    const { container } = render(
      <StoryScreen
        isGenerating={false}
        title=""
        audioUrl=""
        durationSeconds={0}
        onCreateAnother={vi.fn()}
      />
    );
    // Should not show the player or the generating state
    expect(screen.queryByText('Creating your story...')).not.toBeInTheDocument();
    expect(screen.queryByText('Download MP3')).not.toBeInTheDocument();
  });
});
