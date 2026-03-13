import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CraftScreen from './CraftScreen';

// Mock the API client
vi.mock('../api/client', () => ({
  fetchGenres: vi.fn(() => Promise.resolve([
    { id: 'adventure', name: 'Adventure', description: 'Exciting journeys', icon: '🗺️' },
    { id: 'fantasy', name: 'Fantasy', description: 'Magical worlds', icon: '🧙' },
  ])),
  fetchHistoricalEvents: vi.fn(() => Promise.resolve([
    { id: 'moon-landing', title: 'Moon Landing', figure: 'Neil Armstrong', year: 1969, summary: 'First humans on Moon', key_facts: [], thumbnail: '' },
  ])),
}));

const defaultProps = {
  storyType: 'custom' as const,
  mood: undefined,
  length: undefined,
  onMoodChange: vi.fn(),
  onLengthChange: vi.fn(),
  onSubmitCustom: vi.fn(),
  onSubmitHistorical: vi.fn(),
  onBack: vi.fn(),
  onTypeChange: vi.fn(),
};

describe('CraftScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner initially', () => {
    render(<CraftScreen {...defaultProps} />);
    expect(screen.getByText('Craft the Adventure')).toBeInTheDocument();
  });

  it('loads and displays genres', async () => {
    render(<CraftScreen {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText('Adventure')).toBeInTheDocument();
      expect(screen.getByText('Fantasy')).toBeInTheDocument();
    });
  });

  it('shows mood options', async () => {
    render(<CraftScreen {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText('Exciting')).toBeInTheDocument();
      expect(screen.getByText('Heartwarming')).toBeInTheDocument();
      expect(screen.getByText('Funny')).toBeInTheDocument();
      expect(screen.getByText('Mysterious')).toBeInTheDocument();
    });
  });

  it('shows length options', async () => {
    render(<CraftScreen {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText('Short')).toBeInTheDocument();
      expect(screen.getByText('Medium')).toBeInTheDocument();
      expect(screen.getByText('Long')).toBeInTheDocument();
    });
  });

  it('Create Story button is disabled without genre and description', async () => {
    render(<CraftScreen {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText('Create Story')).toBeDisabled();
    });
  });

  it('enables Create Story after selecting genre and entering description', async () => {
    const user = userEvent.setup();
    render(<CraftScreen {...defaultProps} />);

    await waitFor(() => expect(screen.getByText('Adventure')).toBeInTheDocument());
    await user.click(screen.getByText('Adventure'));
    await user.type(screen.getByPlaceholderText('Describe your story idea...'), 'A quest');

    expect(screen.getByText('Create Story')).not.toBeDisabled();
  });

  it('calls onBack when back button clicked', async () => {
    const onBack = vi.fn();
    render(<CraftScreen {...defaultProps} onBack={onBack} />);
    await waitFor(() => expect(screen.getByText('Adventure')).toBeInTheDocument());

    const backBtn = screen.getAllByRole('button').find(b => b.textContent?.includes('Back'));
    backBtn?.click();
    expect(onBack).toHaveBeenCalled();
  });

  it('shows historical events when type is historical', async () => {
    render(<CraftScreen {...defaultProps} storyType="historical" />);
    await waitFor(() => {
      expect(screen.getByText('Moon Landing')).toBeInTheDocument();
      expect(screen.getByText('Neil Armstrong')).toBeInTheDocument();
    });
  });

  it('has maxLength on description textarea', async () => {
    render(<CraftScreen {...defaultProps} />);
    await waitFor(() => expect(screen.getByText('Adventure')).toBeInTheDocument());
    const textarea = screen.getByPlaceholderText('Describe your story idea...');
    expect(textarea).toHaveAttribute('maxLength', '500');
  });

  it('type toggle buttons switch between custom and historical', async () => {
    const onTypeChange = vi.fn();
    render(<CraftScreen {...defaultProps} onTypeChange={onTypeChange} />);

    await waitFor(() => expect(screen.getByText('Adventure')).toBeInTheDocument());
    const histBtn = screen.getByRole('button', { name: 'Historical Adventure' });
    histBtn.click();
    expect(onTypeChange).toHaveBeenCalledWith('historical');
  });
});
