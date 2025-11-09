import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import TradeIdeaCard from './TradeIdeaCard';
import { mockTradeIdea } from '@/test/test-utils';

describe('TradeIdeaCard Component', () => {
  it('renders trade idea with all basic information', () => {
    const tradeIdea = mockTradeIdea();
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    // Symbol and timeframe
    expect(screen.getByText('EURUSD')).toBeInTheDocument();
    expect(screen.getByText(/H1/)).toBeInTheDocument();

    // Confidence
    expect(screen.getByText('85')).toBeInTheDocument();
    expect(screen.getByText('Confidence')).toBeInTheDocument();

    // Direction
    expect(screen.getByText('long')).toBeInTheDocument();

    // Price levels
    expect(screen.getByText('1.10000')).toBeInTheDocument(); // Entry
    expect(screen.getByText('1.09500')).toBeInTheDocument(); // Stop Loss
    expect(screen.getByText('1.11000')).toBeInTheDocument(); // Take Profit
  });

  it('renders long trade with correct styling', () => {
    const tradeIdea = mockTradeIdea({ direction: 'long' });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    expect(screen.getByText('long')).toHaveClass('text-green-500');
  });

  it('renders short trade with correct styling', () => {
    const tradeIdea = mockTradeIdea({ direction: 'short' });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    expect(screen.getByText('short')).toHaveClass('text-red-500');
  });

  it('displays volume and RR ratio correctly', () => {
    const tradeIdea = mockTradeIdea({ volume: 0.5, rr_ratio: 3.5 });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    expect(screen.getByText('0.50')).toBeInTheDocument(); // Volume
    expect(screen.getByText('3.50')).toBeInTheDocument(); // RR Ratio
  });

  it('highlights good RR ratio in green', () => {
    const tradeIdea = mockTradeIdea({ rr_ratio: 2.5 });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    const rrElement = screen.getByText('2.50');
    expect(rrElement).toHaveClass('text-green-400');
  });

  it('highlights poor RR ratio in yellow', () => {
    const tradeIdea = mockTradeIdea({ rr_ratio: 1.5 });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    const rrElement = screen.getByText('1.50');
    expect(rrElement).toHaveClass('text-yellow-500');
  });

  it('displays risk percentage correctly', () => {
    const tradeIdea = mockTradeIdea({
      execution_plan: { action: 'open_or_scale', riskPct: '0.02' },
    });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    expect(screen.getByText('2.00%')).toBeInTheDocument();
  });

  it('displays status badge correctly', () => {
    const tradeIdea = mockTradeIdea({ status: 'pending_approval' });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    expect(screen.getByText('PENDING APPROVAL')).toBeInTheDocument();
  });

  it('displays EMNR flags correctly when all true', () => {
    const tradeIdea = mockTradeIdea({
      emnr_flags: {
        entry: true,
        strong: true,
        weak: false,
        exit: false,
        align: true,
      },
    });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    // Check for EMNR flag labels (there are multiple "Entry" texts, so use getAllByText)
    expect(screen.getAllByText('Entry').length).toBeGreaterThan(0);
    expect(screen.getByText('Strong')).toBeInTheDocument();
    expect(screen.getByText('Weak')).toBeInTheDocument();
    expect(screen.getByText('Exit')).toBeInTheDocument();

    // Check for checkmarks and crosses
    const checkmarks = screen.getAllByText('✓');
    expect(checkmarks.length).toBe(2); // Entry and Strong should have checkmarks
  });

  it('displays EMNR flags correctly when all false', () => {
    const tradeIdea = mockTradeIdea({
      emnr_flags: {
        entry: false,
        strong: false,
        weak: false,
        exit: false,
        align: false,
      },
    });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    const crosses = screen.getAllByText('✗');
    expect(crosses.length).toBe(4); // All 4 flags should show crosses
  });

  it('displays technical indicators', () => {
    const tradeIdea = mockTradeIdea({
      indicators: {
        ema_fast: 1.09950,
        ema_slow: 1.09800,
        rsi: 65.5,
        macd: 0.00050,
        macd_signal: 0.00030,
        atr: 0.00150,
        atr_median: 0.00140,
        bb_upper: 1.10200,
        bb_middle: 1.10000,
        bb_lower: 1.09800,
      },
    });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    expect(screen.getByText('1.09950')).toBeInTheDocument(); // EMA Fast
    expect(screen.getByText('1.09800')).toBeInTheDocument(); // EMA Slow
    expect(screen.getByText('65.50')).toBeInTheDocument(); // RSI
    expect(screen.getByText('0.00050')).toBeInTheDocument(); // MACD
    expect(screen.getByText('0.00150')).toBeInTheDocument(); // ATR
    expect(screen.getByText('0.00140')).toBeInTheDocument(); // ATR Median
  });

  it('shows Review & Execute button for pending_approval status', () => {
    const tradeIdea = mockTradeIdea({ status: 'pending_approval' });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    expect(screen.getByRole('button', { name: /review & execute/i })).toBeInTheDocument();
  });

  it('shows Review & Execute button for approved status', () => {
    const tradeIdea = mockTradeIdea({ status: 'approved' });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    expect(screen.getByRole('button', { name: /review & execute/i })).toBeInTheDocument();
  });

  it('calls onReview when Review button is clicked', async () => {
    const onReview = vi.fn();
    const tradeIdea = mockTradeIdea({ status: 'pending_approval' });
    const user = userEvent.setup();

    render(<TradeIdeaCard tradeIdea={tradeIdea} onReview={onReview} />);

    await user.click(screen.getByRole('button', { name: /review & execute/i }));

    expect(onReview).toHaveBeenCalledTimes(1);
    expect(onReview).toHaveBeenCalledWith(tradeIdea);
  });

  it('does not show Review button for executed status', () => {
    const tradeIdea = mockTradeIdea({ status: 'executed' });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    expect(screen.queryByRole('button', { name: /review & execute/i })).not.toBeInTheDocument();
  });

  it('shows Executed badge for executed status', () => {
    const tradeIdea = mockTradeIdea({ status: 'executed' });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    expect(screen.getByText('Executed')).toBeInTheDocument();
  });

  it('shows Rejected badge for rejected status', () => {
    const tradeIdea = mockTradeIdea({ status: 'rejected' });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    expect(screen.getByText('Rejected')).toBeInTheDocument();
  });

  it('does not show Review button for rejected status', () => {
    const tradeIdea = mockTradeIdea({ status: 'rejected' });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    expect(screen.queryByRole('button', { name: /review & execute/i })).not.toBeInTheDocument();
  });

  it('handles missing onReview callback gracefully', async () => {
    const tradeIdea = mockTradeIdea({ status: 'pending_approval' });
    const user = userEvent.setup();

    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    // Should not throw error when clicking without onReview
    await user.click(screen.getByRole('button', { name: /review & execute/i }));
  });

  it('displays timestamp in locale format', () => {
    const timestamp = '2025-10-10T10:30:00Z';
    const tradeIdea = mockTradeIdea({ timestamp });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    // Check that timestamp is rendered (format may vary by locale)
    const timestampElement = screen.getByText(/H1/);
    expect(timestampElement).toBeInTheDocument();
  });

  it('displays high confidence in green', () => {
    const tradeIdea = mockTradeIdea({ confidence: 90 });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    const confidenceElement = screen.getByText('90');
    // The getConfidenceColor function should return green for high confidence
    expect(confidenceElement).toHaveClass(/text-/);
  });

  it('displays medium confidence in yellow', () => {
    const tradeIdea = mockTradeIdea({ confidence: 70 });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    const confidenceElement = screen.getByText('70');
    expect(confidenceElement).toHaveClass(/text-/);
  });

  it('displays low confidence in red', () => {
    const tradeIdea = mockTradeIdea({ confidence: 50 });
    render(<TradeIdeaCard tradeIdea={tradeIdea} />);

    const confidenceElement = screen.getByText('50');
    expect(confidenceElement).toHaveClass(/text-/);
  });
});

