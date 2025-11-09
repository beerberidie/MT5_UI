import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import Settings from './Settings';

describe('Settings Page Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Page Initialization', () => {
    it('renders settings page with default tab', () => {
      render(<Settings />);

      // Should show RISK tab by default
      expect(screen.getByLabelText(/maximum risk %/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/default risk %/i)).toBeInTheDocument();
    });

    it('displays all tab options', () => {
      render(<Settings />);

      expect(screen.getByRole('button', { name: /risk management/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^accounts$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /api integrations/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^appearance$/i })).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('switches between tabs', async () => {
      const user = userEvent.setup();
      render(<Settings />);

      // Click Accounts tab
      const accountsTab = screen.getByRole('button', { name: /^accounts$/i });
      await user.click(accountsTab);

      // Should show accounts section (use role to avoid duplicate text)
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /mt5 accounts/i })).toBeInTheDocument();
      });

      // Click APIs tab
      const apisTab = screen.getByRole('button', { name: /api integrations/i });
      await user.click(apisTab);

      // Should show API integrations section (multiple headings exist, just verify tab is active)
      await waitFor(() => {
        expect(apisTab).toHaveClass('bg-primary');
      });

      // Click Appearance tab
      const appearanceTab = screen.getByRole('button', { name: /^appearance$/i });
      await user.click(appearanceTab);

      // Should show appearance section (use label to avoid duplicate text)
      await waitFor(() => {
        expect(screen.getByText(/ui density/i)).toBeInTheDocument();
      });

      // Click back to Risk tab
      const riskTab = screen.getByRole('button', { name: /risk management/i });
      await user.click(riskTab);

      // Should show risk settings
      await waitFor(() => {
        expect(screen.getByLabelText(/maximum risk %/i)).toBeInTheDocument();
      });
    });
  });

  describe('Risk Settings Workflow', () => {
    it('updates maximum risk percentage', async () => {
      render(<Settings />);

      const maxRiskInput = screen.getByLabelText(/maximum risk %/i) as HTMLInputElement;

      // Use fireEvent.change to directly set value (avoids userEvent appending issue)
      fireEvent.change(maxRiskInput, { target: { value: '2.5' } });

      // Wait for value to update
      await waitFor(() => {
        expect(maxRiskInput).toHaveValue(2.5);
      });
    });

    it('updates default risk percentage', async () => {
      render(<Settings />);

      const defaultRiskInput = screen.getByLabelText(/default risk %/i) as HTMLInputElement;

      fireEvent.change(defaultRiskInput, { target: { value: '1.5' } });

      await waitFor(() => {
        expect(defaultRiskInput).toHaveValue(1.5);
      });
    });

    it('updates SL/TP scaling strategy', async () => {
      const user = userEvent.setup();
      render(<Settings />);

      const strategySelect = screen.getByLabelText(/sl\/tp scaling strategy/i);

      await user.selectOptions(strategySelect, 'PIPS');

      expect(strategySelect).toHaveValue('PIPS');
    });

    it('updates risk-reward ratio target', async () => {
      render(<Settings />);

      const rrInput = screen.getByLabelText(/risk-reward target/i) as HTMLInputElement;

      fireEvent.change(rrInput, { target: { value: '3.0' } });

      await waitFor(() => {
        expect(rrInput).toHaveValue(3.0);
      });
    });

    it('saves risk settings', async () => {
      const user = userEvent.setup();
      render(<Settings />);

      // Update a value
      const maxRiskInput = screen.getByLabelText(/maximum risk %/i) as HTMLInputElement;
      fireEvent.change(maxRiskInput, { target: { value: '2.5' } });

      // Click save button
      const saveButton = screen.getByRole('button', { name: /^save$/i });
      await user.click(saveButton);

      // Should show saved confirmation (look for "Saved" text that appears temporarily)
      await waitFor(() => {
        // The component shows "Saved ✓" temporarily after saving
        const savedText = screen.queryByText(/saved/i);
        expect(savedText).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('has reset to defaults button', async () => {
      render(<Settings />);

      // Verify reset button exists
      const resetButton = screen.getByRole('button', { name: /reset to defaults/i });
      expect(resetButton).toBeInTheDocument();
    });

    it('validates maximum risk percentage range', async () => {
      const user = userEvent.setup();
      render(<Settings />);

      const maxRiskInput = screen.getByLabelText(/maximum risk %/i) as HTMLInputElement;

      // Try to set value above max (10) - HTML input will clamp to max
      fireEvent.change(maxRiskInput, { target: { value: '15' } });

      // HTML number input with max="10" will clamp the value to 10
      await waitFor(() => {
        expect(maxRiskInput).toHaveValue(10);
      });
    });

    it('validates default risk percentage range', async () => {
      const user = userEvent.setup();
      render(<Settings />);

      const defaultRiskInput = screen.getByLabelText(/default risk %/i) as HTMLInputElement;

      // Try to set value below min (0.1) - HTML input will clamp to min
      fireEvent.change(defaultRiskInput, { target: { value: '0.05' } });

      // HTML number input with min="0.1" will clamp the value to 0.1
      await waitFor(() => {
        expect(defaultRiskInput).toHaveValue(0.1);
      });
    });

    it('validates risk-reward ratio range', async () => {
      const user = userEvent.setup();
      render(<Settings />);

      const rrInput = screen.getByLabelText(/risk-reward target/i) as HTMLInputElement;

      // Try to set value above max (5) - HTML input will clamp to max
      fireEvent.change(rrInput, { target: { value: '6.0' } });

      // HTML number input with max="5" will clamp the value to 5
      await waitFor(() => {
        expect(rrInput).toHaveValue(5);
      });
    });
  });

  describe('Accounts Section Workflow', () => {
    it('displays accounts section when tab is clicked', async () => {
      const user = userEvent.setup();
      render(<Settings />);

      const accountsTab = screen.getByRole('button', { name: /^accounts$/i });
      await user.click(accountsTab);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /mt5 accounts/i })).toBeInTheDocument();
      });
    });

    it('shows add account button', async () => {
      const user = userEvent.setup();
      render(<Settings />);

      const accountsTab = screen.getByRole('button', { name: /^accounts$/i });
      await user.click(accountsTab);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add account/i })).toBeInTheDocument();
      });
    });
  });

  describe('API Integrations Section Workflow', () => {
    it('displays API integrations section when tab is clicked', async () => {
      const user = userEvent.setup();
      render(<Settings />);

      const apisTab = screen.getByRole('button', { name: /api integrations/i });
      await user.click(apisTab);

      // Multiple headings with "API Integrations" exist, just verify tab is active
      await waitFor(() => {
        expect(apisTab).toHaveClass('bg-primary');
      });
    });

    it('shows add integration button', async () => {
      const user = userEvent.setup();
      render(<Settings />);

      const apisTab = screen.getByRole('button', { name: /api integrations/i });
      await user.click(apisTab);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add integration/i })).toBeInTheDocument();
      });
    });
  });

  describe('Appearance Section Workflow', () => {
    it('displays appearance section when tab is clicked', async () => {
      const user = userEvent.setup();
      render(<Settings />);

      const appearanceTab = screen.getByRole('button', { name: /^appearance$/i });
      await user.click(appearanceTab);

      await waitFor(() => {
        // Look for UI Density label which is unique to appearance section
        expect(screen.getByText(/ui density/i)).toBeInTheDocument();
      });
    });

    it('shows theme selection options', async () => {
      const user = userEvent.setup();
      render(<Settings />);

      const appearanceTab = screen.getByRole('button', { name: /^appearance$/i });
      await user.click(appearanceTab);

      await waitFor(() => {
        // Look for theme radio buttons
        expect(screen.getByRole('radio', { name: /dark.*low-light/i })).toBeInTheDocument();
        expect(screen.getByRole('radio', { name: /light.*bright/i })).toBeInTheDocument();
      });
    });
  });

  describe('Keyboard Navigation', () => {
    it('supports tab key navigation between inputs', async () => {
      const user = userEvent.setup();
      render(<Settings />);

      const maxRiskInput = screen.getByLabelText(/maximum risk %/i);
      const defaultRiskInput = screen.getByLabelText(/default risk %/i);

      // Focus first input
      maxRiskInput.focus();
      expect(maxRiskInput).toHaveFocus();

      // Tab to next input
      await user.tab();
      expect(defaultRiskInput).toHaveFocus();
    });
  });
});

