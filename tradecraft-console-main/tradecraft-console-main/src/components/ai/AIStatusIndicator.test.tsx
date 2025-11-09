import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import AIStatusIndicator from './AIStatusIndicator';
import * as api from '@/lib/api';

// Mock the API module
vi.mock('@/lib/api', () => ({
  getAIStatus: vi.fn(),
}));

describe('AIStatusIndicator Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    vi.mocked(api.getAIStatus).mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<AIStatusIndicator />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();
    // Check for the pulsing brain icon (SVG)
    const svg = document.querySelector('.lucide-brain.animate-pulse');
    expect(svg).toBeInTheDocument();
  });

  it('displays AI disabled state correctly', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue({
      enabled: false,
      mode: 'semi-auto',
      enabled_symbols: [],
      active_trade_ideas: 0,
      autonomy_loop_running: false,
    });

    render(<AIStatusIndicator />);

    await waitFor(() => {
      expect(screen.getByText('AI Trading')).toBeInTheDocument();
    });

    expect(screen.getByText('OFF')).toBeInTheDocument();
    expect(screen.queryByText(/symbols/)).not.toBeInTheDocument();
  });

  it('displays AI enabled state with no symbols', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue({
      enabled: true,
      mode: 'semi-auto',
      enabled_symbols: [],
      active_trade_ideas: 0,
      autonomy_loop_running: false,
    });

    render(<AIStatusIndicator />);

    await waitFor(() => {
      expect(screen.getByText('AI Trading')).toBeInTheDocument();
    });

    expect(screen.queryByText('OFF')).not.toBeInTheDocument();
    expect(screen.getByText('0 symbols')).toBeInTheDocument();
  });

  it('displays AI enabled state with one symbol', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue({
      enabled: true,
      mode: 'semi-auto',
      enabled_symbols: ['EURUSD'],
      active_trade_ideas: 0,
      autonomy_loop_running: false,
    });

    render(<AIStatusIndicator />);

    await waitFor(() => {
      expect(screen.getByText('1 symbol')).toBeInTheDocument();
    });
  });

  it('displays AI enabled state with multiple symbols', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue({
      enabled: true,
      mode: 'semi-auto',
      enabled_symbols: ['EURUSD', 'GBPUSD', 'USDJPY'],
      active_trade_ideas: 0,
      autonomy_loop_running: false,
    });

    render(<AIStatusIndicator />);

    await waitFor(() => {
      expect(screen.getByText('3 symbols')).toBeInTheDocument();
    });
  });

  it('displays trade ideas count correctly (singular)', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue({
      enabled: true,
      mode: 'semi-auto',
      enabled_symbols: ['EURUSD'],
      active_trade_ideas: 1,
      autonomy_loop_running: false,
    });

    render(<AIStatusIndicator />);

    await waitFor(() => {
      expect(screen.getByText('1 idea')).toBeInTheDocument();
    });

    // Should show badge with count
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('displays trade ideas count correctly (plural)', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue({
      enabled: true,
      mode: 'semi-auto',
      enabled_symbols: ['EURUSD', 'GBPUSD'],
      active_trade_ideas: 5,
      autonomy_loop_running: false,
    });

    render(<AIStatusIndicator />);

    await waitFor(() => {
      expect(screen.getByText('5 ideas')).toBeInTheDocument();
    });

    // Should show badge with count
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('displays 9+ for more than 9 trade ideas', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue({
      enabled: true,
      mode: 'semi-auto',
      enabled_symbols: ['EURUSD'],
      active_trade_ideas: 15,
      autonomy_loop_running: false,
    });

    render(<AIStatusIndicator />);

    await waitFor(() => {
      expect(screen.getByText('15 ideas')).toBeInTheDocument();
    });

    // Badge should show 9+
    expect(screen.getByText('9+')).toBeInTheDocument();
  });

  it('links to AI page', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue({
      enabled: true,
      mode: 'semi-auto',
      enabled_symbols: ['EURUSD'],
      active_trade_ideas: 0,
      autonomy_loop_running: false,
    });

    render(<AIStatusIndicator />);

    await waitFor(() => {
      expect(screen.getByText('AI Trading')).toBeInTheDocument();
    });

    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/ai');
  });

  // TODO: Fix timer-based test
  it.skip('refreshes status every 10 seconds', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue({
      enabled: true,
      mode: 'semi-auto',
      enabled_symbols: ['EURUSD'],
      active_trade_ideas: 0,
      autonomy_loop_running: false,
    });

    render(<AIStatusIndicator />);

    // Initial load
    await waitFor(() => {
      expect(api.getAIStatus).toHaveBeenCalledTimes(1);
    });

    // Advance 10 seconds
    vi.advanceTimersByTime(10000);

    await waitFor(() => {
      expect(api.getAIStatus).toHaveBeenCalledTimes(2);
    });

    // Advance another 10 seconds
    vi.advanceTimersByTime(10000);

    await waitFor(() => {
      expect(api.getAIStatus).toHaveBeenCalledTimes(3);
    });
  });

  it('handles API errors gracefully', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(api.getAIStatus).mockRejectedValue(new Error('API Error'));

    render(<AIStatusIndicator />);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to load AI status:',
        expect.any(Error)
      );
    });

    // Should still render but with default values
    expect(screen.getByText('AI Trading')).toBeInTheDocument();
    expect(screen.getByText('OFF')).toBeInTheDocument();

    consoleErrorSpy.mockRestore();
  });

  // TODO: Fix timer-based test
  it.skip('cleans up interval on unmount', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue({
      enabled: true,
      mode: 'semi-auto',
      enabled_symbols: ['EURUSD'],
      active_trade_ideas: 0,
      autonomy_loop_running: false,
    });

    const { unmount } = render(<AIStatusIndicator />);

    await waitFor(() => {
      expect(api.getAIStatus).toHaveBeenCalledTimes(1);
    });

    unmount();

    // Advance time after unmount
    vi.advanceTimersByTime(10000);

    // Should not call API again
    expect(api.getAIStatus).toHaveBeenCalledTimes(1);
  });

  it('shows green pulse indicator when AI is enabled', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue({
      enabled: true,
      mode: 'semi-auto',
      enabled_symbols: ['EURUSD'],
      active_trade_ideas: 0,
      autonomy_loop_running: false,
    });

    render(<AIStatusIndicator />);

    await waitFor(() => {
      expect(screen.getByText('AI Trading')).toBeInTheDocument();
    });

    // Check for pulse indicator (green dot)
    const pulseIndicator = document.querySelector('.bg-green-500.animate-pulse');
    expect(pulseIndicator).toBeInTheDocument();
  });

  it('does not show pulse indicator when AI is disabled', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue({
      enabled: false,
      mode: 'semi-auto',
      enabled_symbols: [],
      active_trade_ideas: 0,
      autonomy_loop_running: false,
    });

    render(<AIStatusIndicator />);

    await waitFor(() => {
      expect(screen.getByText('OFF')).toBeInTheDocument();
    });

    // Should not have pulse indicator
    const pulseIndicator = document.querySelector('.bg-green-500.animate-pulse');
    expect(pulseIndicator).not.toBeInTheDocument();
  });
});

