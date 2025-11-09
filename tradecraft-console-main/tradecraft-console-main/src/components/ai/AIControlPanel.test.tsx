import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import AIControlPanel from './AIControlPanel';
import * as api from '@/lib/api';
import { mockAIStatus } from '@/test/test-utils';

// Mock the API module
vi.mock('@/lib/api', () => ({
  getAIStatus: vi.fn(),
  triggerKillSwitch: vi.fn(),
}));

// Mock window.confirm
const mockConfirm = vi.fn();
global.confirm = mockConfirm;

describe('AIControlPanel Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockConfirm.mockReturnValue(true); // Default to confirming
  });

  it('shows loading state initially', () => {
    vi.mocked(api.getAIStatus).mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<AIControlPanel />);

    expect(screen.getByText('AI Control Panel')).toBeInTheDocument();
    expect(screen.getByText('Loading AI status...')).toBeInTheDocument();
  });

  it('displays AI enabled status correctly', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ enabled: true, mode: 'semi-auto' })
    );

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });

    expect(screen.getByText('semi-auto')).toBeInTheDocument();
  });

  it('displays AI disabled status correctly', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ enabled: false })
    );

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('DISABLED')).toBeInTheDocument();
    });

    expect(screen.getByText('AI Trading is currently disabled')).toBeInTheDocument();
  });

  it('displays mode correctly', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ mode: 'full-auto' })
    );

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('full-auto')).toBeInTheDocument();
    });
  });

  it('displays active trade ideas count', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ active_trade_ideas: 5 })
    );

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });

  it('displays autonomy loop running status', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ autonomy_loop_running: true })
    );

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('Running')).toBeInTheDocument();
    });
  });

  it('displays autonomy loop stopped status', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ autonomy_loop_running: false })
    );

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('Stopped')).toBeInTheDocument();
    });
  });

  it('displays enabled symbols', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ enabled_symbols: ['EURUSD', 'GBPUSD', 'USDJPY'] })
    );

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('EURUSD')).toBeInTheDocument();
      expect(screen.getByText('GBPUSD')).toBeInTheDocument();
      expect(screen.getByText('USDJPY')).toBeInTheDocument();
    });

    expect(screen.getByText('3 active')).toBeInTheDocument();
  });

  it('shows empty state when no symbols enabled', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ enabled_symbols: [] })
    );

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('No symbols enabled')).toBeInTheDocument();
    });

    expect(screen.getByText('Enable AI for symbols below to start monitoring')).toBeInTheDocument();
  });

  // TODO: Fix timer-based test
  it.skip('refreshes status every 5 seconds', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(mockAIStatus());

    render(<AIControlPanel />);

    // Initial load
    await waitFor(() => {
      expect(api.getAIStatus).toHaveBeenCalledTimes(1);
    });

    // Advance 5 seconds
    vi.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(api.getAIStatus).toHaveBeenCalledTimes(2);
    });

    // Advance another 5 seconds
    vi.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(api.getAIStatus).toHaveBeenCalledTimes(3);
    });
  });

  it('handles manual refresh', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(mockAIStatus());
    const user = userEvent.setup({ delay: null });

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(api.getAIStatus).toHaveBeenCalledTimes(1);
    });

    const refreshButton = screen.getByRole('button', { name: '' }); // Refresh button has no text
    await user.click(refreshButton);

    await waitFor(() => {
      expect(api.getAIStatus).toHaveBeenCalledTimes(2);
    });
  });

  it('disables kill switch when AI is disabled', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ enabled: false })
    );

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('DISABLED')).toBeInTheDocument();
    });

    const killSwitchButton = screen.getByRole('button', { name: /kill switch/i });
    expect(killSwitchButton).toBeDisabled();
  });

  it('enables kill switch when AI is enabled', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ enabled: true })
    );

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });

    const killSwitchButton = screen.getByRole('button', { name: /kill switch/i });
    expect(killSwitchButton).not.toBeDisabled();
  });

  it('triggers kill switch with confirmation', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ enabled: true })
    );
    vi.mocked(api.triggerKillSwitch).mockResolvedValue({ success: true });
    mockConfirm.mockReturnValue(true);
    const user = userEvent.setup({ delay: null });

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });

    const killSwitchButton = screen.getByRole('button', { name: /kill switch/i });
    await user.click(killSwitchButton);

    expect(mockConfirm).toHaveBeenCalledWith(
      expect.stringContaining('Are you sure you want to disable ALL AI trading?')
    );

    await waitFor(() => {
      expect(api.triggerKillSwitch).toHaveBeenCalledWith(
        'Manual kill switch activation from UI'
      );
    });
  });

  it('does not trigger kill switch when confirmation is cancelled', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ enabled: true })
    );
    mockConfirm.mockReturnValue(false); // User cancels
    const user = userEvent.setup({ delay: null });

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });

    const killSwitchButton = screen.getByRole('button', { name: /kill switch/i });
    await user.click(killSwitchButton);

    expect(mockConfirm).toHaveBeenCalled();
    expect(api.triggerKillSwitch).not.toHaveBeenCalled();
  });

  it('handles kill switch API error', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ enabled: true })
    );
    vi.mocked(api.triggerKillSwitch).mockRejectedValue(new Error('API Error'));
    mockConfirm.mockReturnValue(true);
    const user = userEvent.setup({ delay: null });

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });

    const killSwitchButton = screen.getByRole('button', { name: /kill switch/i });
    await user.click(killSwitchButton);

    await waitFor(() => {
      expect(api.triggerKillSwitch).toHaveBeenCalled();
    });

    // Toast error should be shown (we can't easily test toast content in unit tests)
  });

  it('handles API error on initial load', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(api.getAIStatus).mockRejectedValue(new Error('API Error'));

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to load AI status:',
        expect.any(Error)
      );
    });

    consoleErrorSpy.mockRestore();
  });

  // TODO: Fix timer-based test
  it.skip('cleans up interval on unmount', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(mockAIStatus());

    const { unmount } = render(<AIControlPanel />);

    await waitFor(() => {
      expect(api.getAIStatus).toHaveBeenCalledTimes(1);
    });

    unmount();

    // Advance time after unmount
    vi.advanceTimersByTime(5000);

    // Should not call API again
    expect(api.getAIStatus).toHaveBeenCalledTimes(1);
  });

  it('shows warning when AI is disabled', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ enabled: false })
    );

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('AI Trading is currently disabled')).toBeInTheDocument();
    });

    expect(
      screen.getByText('Enable AI for specific symbols to start receiving trade ideas')
    ).toBeInTheDocument();
  });

  it('does not show warning when AI is enabled', async () => {
    vi.mocked(api.getAIStatus).mockResolvedValue(
      mockAIStatus({ enabled: true })
    );

    render(<AIControlPanel />);

    await waitFor(() => {
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    });

    expect(
      screen.queryByText('AI Trading is currently disabled')
    ).not.toBeInTheDocument();
  });
});

