import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HeroScreen from './HeroScreen';

describe('HeroScreen', () => {
  it('renders title and inputs', () => {
    render(<HeroScreen onSubmit={vi.fn()} />);
    expect(screen.getByText("Who's the hero?")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Your child's name")).toBeInTheDocument();
    expect(screen.getByText('Age')).toBeInTheDocument();
  });

  it('shows age buttons from 3 to 12', () => {
    render(<HeroScreen onSubmit={vi.fn()} />);
    for (let i = 3; i <= 12; i++) {
      expect(screen.getByRole('button', { name: String(i) })).toBeInTheDocument();
    }
  });

  it('disables story type buttons until name and age are set', () => {
    render(<HeroScreen onSubmit={vi.fn()} />);
    const customBtn = screen.getByRole('button', { name: /Custom Story/i });
    const histBtn = screen.getByRole('button', { name: /Historical Adventure/i });
    expect(customBtn).toBeDisabled();
    expect(histBtn).toBeDisabled();
  });

  it('enables buttons after entering name and selecting age', async () => {
    const user = userEvent.setup();
    render(<HeroScreen onSubmit={vi.fn()} />);

    await user.type(screen.getByPlaceholderText("Your child's name"), 'Arjun');
    await user.click(screen.getByRole('button', { name: '7' }));

    const customBtn = screen.getByRole('button', { name: /Custom Story/i });
    expect(customBtn).not.toBeDisabled();
  });

  it('calls onSubmit with profile and type on click', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<HeroScreen onSubmit={onSubmit} />);

    await user.type(screen.getByPlaceholderText("Your child's name"), 'Arjun');
    await user.click(screen.getByRole('button', { name: '7' }));
    await user.click(screen.getByRole('button', { name: /Custom Story/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Arjun', age: 7 }),
      'custom'
    );
  });

  it('toggles personalize section', async () => {
    const user = userEvent.setup();
    render(<HeroScreen onSubmit={vi.fn()} />);

    expect(screen.queryByPlaceholderText('Favorite animal')).not.toBeInTheDocument();
    await user.click(screen.getByText('Personalize the story'));
    expect(screen.getByPlaceholderText('Favorite animal')).toBeInTheDocument();
  });

  it('includes personalization details in profile', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<HeroScreen onSubmit={onSubmit} />);

    await user.type(screen.getByPlaceholderText("Your child's name"), 'Arjun');
    await user.click(screen.getByRole('button', { name: '7' }));
    await user.click(screen.getByText('Personalize the story'));
    await user.type(screen.getByPlaceholderText('Favorite animal'), 'tiger');
    await user.click(screen.getByRole('button', { name: /Custom Story/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Arjun', age: 7, favorite_animal: 'tiger' }),
      'custom'
    );
  });

  it('has maxLength on name input', () => {
    render(<HeroScreen onSubmit={vi.fn()} />);
    const nameInput = screen.getByPlaceholderText("Your child's name");
    expect(nameInput).toHaveAttribute('maxLength', '50');
  });
});
