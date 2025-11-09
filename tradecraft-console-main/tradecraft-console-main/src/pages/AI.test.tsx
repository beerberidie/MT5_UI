import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import AI from './AI';
import * as api from '@/lib/api';

// Mock the API module
vi.mock('@/lib/api');

// Mock toast
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  toast: mockToast,
  useToast: () => ({ toast: mockToast }),
}));

describe('AI Page Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockToast.mockClear();

    // Default API mocks
    vi.mocked(api.getSymbols).mockResolvedValue([
      { symbol: 'EURUSD', enabled: false },
      { symbol: 'GBPUSD', enabled: false },
      { symbol: 'USDJPY', enabled: false },
    ] as any);

    vi.mocked(api.getAIDecisions).mockResolvedValue([]);
    vi.mocked(api.getAccount).mockResolvedValue({ balance: 10000 } as any);
    vi.mocked(api.getAutonomyStatus).mockResolvedValue({
      running: false,
      interval_minutes: 15,
      enabled_symbols: [],
      last_run: null,
      next_run: null,
    });
  });

  describe('Page Initialization', () => {
    it('loads and displays symbols on mount', async () => {
      render(<AI />);

      await waitFor(() => {
        expect(api.getSymbols).toHaveBeenCalledWith(false);
      });

      // Should load other data as well
      expect(api.getAIDecisions).toHaveBeenCalledWith(50);
      expect(api.getAccount).toHaveBeenCalled();
      expect(api.getAutonomyStatus).toHaveBeenCalled();
    });

    it('handles API errors gracefully on initial load', async () => {
      vi.mocked(api.getSymbols).mockRejectedValue(new Error('Network error'));

      render(<AI />);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Failed to Load Symbols',
            variant: 'destructive',
          })
        );
      });
    });

    it('handles non-array response from getSymbols', async () => {
      vi.mocked(api.getSymbols).mockResolvedValue({ error: 'Invalid data' } as any);

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(<AI />);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'getSymbols returned non-array data:',
          expect.any(Object)
        );
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Tab Navigation', () => {
    it('switches between overview, strategies, and history tabs', async () => {
      const user = userEvent.setup();
      render(<AI />);

      // Wait for initial load
      await waitFor(() => {
        expect(api.getSymbols).toHaveBeenCalled();
      });

      // Find and click strategies tab
      const strategiesTab = screen.getByRole('button', { name: /strategies/i });
      await user.click(strategiesTab);

      // Verify strategies content is shown
      expect(screen.getByText(/strategy editor/i)).toBeInTheDocument();

      // Click history tab
      const historyTab = screen.getByRole('button', { name: /history/i });
      await user.click(historyTab);

      // Verify history content is shown
      expect(screen.getByText(/decision history/i)).toBeInTheDocument();

      // Click back to overview
      const overviewTab = screen.getByRole('button', { name: /overview/i });
      await user.click(overviewTab);

      // Verify overview content is shown
      expect(screen.getByText(/ai control panel/i)).toBeInTheDocument();
    });
  });

  describe('Symbol Evaluation Workflow', () => {
    it('evaluates a symbol and displays trade idea', async () => {
      const user = userEvent.setup();
      const mockTradeIdea = {
        id: 'idea-123',
        symbol: 'EURUSD',
        timeframe: 'H1',
        confidence: 85,
        action: 'open_or_scale',
        direction: 'long',
        entry_price: 1.1000,
        stop_loss: 1.0950,
        take_profit: 1.1100,
        volume: 0.1,
        rr_ratio: 2.0,
        status: 'pending_approval',
        timestamp: '2025-10-10T10:00:00Z',
        emnr_flags: {
          entry: true,
          strong: true,
          weak: false,
          exit: false,
          align: true,
        },
        indicators: {
          ema_fast: 1.0995,
          ema_slow: 1.0980,
          rsi: 65,
          macd: 0.0005,
          macd_signal: 0.0003,
          atr: 0.0015,
          atr_median: 0.0014,
          bb_upper: 1.1020,
          bb_middle: 1.1000,
          bb_lower: 1.0980,
        },
        execution_plan: {
          action: 'open_or_scale',
          riskPct: 0.01,
        },
        notes: 'Test trade idea',
      };

      vi.mocked(api.evaluateSymbol).mockResolvedValue({
        confidence: 85,
        trade_idea: mockTradeIdea,
        message: 'Trade idea generated',
      } as any);

      render(<AI />);

      // Wait for symbols to load
      await waitFor(() => {
        expect(screen.getByText('EURUSD')).toBeInTheDocument();
      });

      // Select symbol
      const symbolSelect = screen.getByRole('combobox', { name: /select symbol/i });
      await user.selectOptions(symbolSelect, 'EURUSD');

      // Click evaluate button
      const evaluateButton = screen.getByRole('button', { name: /evaluate/i });
      await user.click(evaluateButton);

      // Verify API was called
      await waitFor(() => {
        expect(api.evaluateSymbol).toHaveBeenCalledWith('EURUSD', 'H1', false);
      });

      // Verify success toast
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Evaluation Complete',
          description: expect.stringContaining('85% confidence'),
        })
      );

      // Verify trade idea is displayed
      await waitFor(() => {
        expect(screen.getByText('long')).toBeInTheDocument();
        expect(screen.getByText('85')).toBeInTheDocument();
      });
    });

    it('shows error when no symbol is selected', async () => {
      const user = userEvent.setup();
      render(<AI />);

      // Wait for initial load
      await waitFor(() => {
        expect(api.getSymbols).toHaveBeenCalled();
      });

      // Clear symbol selection (if possible)
      // Then click evaluate
      const evaluateButton = screen.getByRole('button', { name: /evaluate/i });
      await user.click(evaluateButton);

      // Should show error toast
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'No Symbol Selected',
            variant: 'destructive',
          })
        );
      });
    });

    it('handles evaluation with no trade idea', async () => {
      const user = userEvent.setup();

      vi.mocked(api.evaluateSymbol).mockResolvedValue({
        confidence: 45,
        trade_idea: null,
        message: 'Conditions not met for trade idea',
      } as any);

      render(<AI />);

      await waitFor(() => {
        expect(screen.getByText('EURUSD')).toBeInTheDocument();
      });

      const evaluateButton = screen.getByRole('button', { name: /evaluate/i });
      await user.click(evaluateButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'No Trade Idea',
            description: 'Conditions not met for trade idea',
          })
        );
      });
    });

    it('handles evaluation API error', async () => {
      const user = userEvent.setup();

      vi.mocked(api.evaluateSymbol).mockRejectedValue(new Error('Evaluation failed'));

      render(<AI />);

      await waitFor(() => {
        expect(screen.getByText('EURUSD')).toBeInTheDocument();
      });

      const evaluateButton = screen.getByRole('button', { name: /evaluate/i });
      await user.click(evaluateButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Evaluation Failed',
            variant: 'destructive',
          })
        );
      });
    });
  });

  describe('AI Enable/Disable Workflow', () => {
    it('enables AI for a symbol', async () => {
      const user = userEvent.setup();
      vi.mocked(api.enableAI).mockResolvedValue({ success: true } as any);

      render(<AI />);

      await waitFor(() => {
        expect(screen.getByText('EURUSD')).toBeInTheDocument();
      });

      // Find and click enable AI button for EURUSD
      const enableButton = screen.getByRole('button', { name: /enable ai.*eurusd/i });
      await user.click(enableButton);

      await waitFor(() => {
        expect(api.enableAI).toHaveBeenCalledWith('EURUSD', 'H1', false);
      });

      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'AI Enabled',
          description: expect.stringContaining('EURUSD'),
        })
      );
    });

    it('disables AI for a symbol', async () => {
      const user = userEvent.setup();
      vi.mocked(api.disableAI).mockResolvedValue({ success: true } as any);

      render(<AI />);

      await waitFor(() => {
        expect(screen.getByText('EURUSD')).toBeInTheDocument();
      });

      // Find and click disable AI button
      const disableButton = screen.getByRole('button', { name: /disable ai.*eurusd/i });
      await user.click(disableButton);

      await waitFor(() => {
        expect(api.disableAI).toHaveBeenCalledWith('EURUSD');
      });

      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'AI Disabled',
          variant: 'destructive',
        })
      );
    });

    it('handles enable AI error', async () => {
      const user = userEvent.setup();
      vi.mocked(api.enableAI).mockRejectedValue(new Error('Failed to enable'));

      render(<AI />);

      await waitFor(() => {
        expect(screen.getByText('EURUSD')).toBeInTheDocument();
      });

      const enableButton = screen.getByRole('button', { name: /enable ai.*eurusd/i });
      await user.click(enableButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Error',
            variant: 'destructive',
          })
        );
      });
    });
  });

  describe('Autonomy Loop Workflow', () => {
    it('starts autonomy loop with specified interval', async () => {
      const user = userEvent.setup();
      vi.mocked(api.startAutonomyLoop).mockResolvedValue({
        success: true,
        message: 'Autonomy loop started',
      });

      vi.mocked(api.getAutonomyStatus).mockResolvedValue({
        running: true,
        interval_minutes: 15,
        enabled_symbols: ['EURUSD'],
        last_run: '2025-10-10T10:00:00Z',
        next_run: '2025-10-10T10:15:00Z',
      });

      render(<AI />);

      await waitFor(() => {
        expect(api.getAutonomyStatus).toHaveBeenCalled();
      });

      // Find interval input and set value
      const intervalInput = screen.getByRole('spinbutton', { name: /interval/i });
      await user.clear(intervalInput);
      await user.type(intervalInput, '20');

      // Click start button
      const startButton = screen.getByRole('button', { name: /start.*autonomy/i });
      await user.click(startButton);

      await waitFor(() => {
        expect(api.startAutonomyLoop).toHaveBeenCalledWith(20);
      });

      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Autonomy Loop Started',
          description: expect.stringContaining('20 minutes'),
        })
      );
    });

    it('stops autonomy loop', async () => {
      const user = userEvent.setup();
      vi.mocked(api.getAutonomyStatus).mockResolvedValue({
        running: true,
        interval_minutes: 15,
        enabled_symbols: ['EURUSD'],
        last_run: '2025-10-10T10:00:00Z',
        next_run: '2025-10-10T10:15:00Z',
      });

      vi.mocked(api.stopAutonomyLoop).mockResolvedValue({
        success: true,
        message: 'Autonomy loop stopped',
      });

      render(<AI />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /stop.*autonomy/i })).toBeInTheDocument();
      });

      const stopButton = screen.getByRole('button', { name: /stop.*autonomy/i });
      await user.click(stopButton);

      await waitFor(() => {
        expect(api.stopAutonomyLoop).toHaveBeenCalled();
      });

      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Autonomy Loop Stopped',
        })
      );
    });

    it('handles start autonomy loop error', async () => {
      const user = userEvent.setup();
      vi.mocked(api.startAutonomyLoop).mockRejectedValue(new Error('Failed to start'));

      render(<AI />);

      await waitFor(() => {
        expect(api.getAutonomyStatus).toHaveBeenCalled();
      });

      const startButton = screen.getByRole('button', { name: /start.*autonomy/i });
      await user.click(startButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Error',
            variant: 'destructive',
          })
        );
      });
    });

    it('triggers immediate evaluation', async () => {
      const user = userEvent.setup();
      vi.mocked(api.triggerImmediateEvaluation).mockResolvedValue({
        success: true,
        message: 'Evaluation triggered',
        results: [],
      });

      render(<AI />);

      await waitFor(() => {
        expect(api.getAutonomyStatus).toHaveBeenCalled();
      });

      const evaluateNowButton = screen.getByRole('button', { name: /evaluate now/i });
      await user.click(evaluateNowButton);

      await waitFor(() => {
        expect(api.triggerImmediateEvaluation).toHaveBeenCalled();
      });

      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: expect.stringContaining('Evaluation'),
        })
      );
    });
  });
});

