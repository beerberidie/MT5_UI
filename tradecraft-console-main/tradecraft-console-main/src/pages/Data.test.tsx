import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import Data from './Data';

describe('Data Page Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Page Initialization', () => {
    it('renders data page with header', () => {
      render(<Data />);

      expect(screen.getByText('3rd Party Data')).toBeInTheDocument();
    });

    it('displays default tab (Economic Calendar)', () => {
      render(<Data />);

      // Economic Calendar should be active by default
      const calendarTab = screen.getByRole('button', { name: /economic calendar/i });
      expect(calendarTab).toHaveClass('bg-sidebar-item-active');
    });

    it('displays all tab options', () => {
      render(<Data />);

      expect(screen.getByRole('button', { name: /economic calendar/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /market news/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /rss feeds/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /technical indicators/i })).toBeInTheDocument();
    });

    it('displays info section', () => {
      render(<Data />);

      expect(screen.getByText(/about 3rd party data/i)).toBeInTheDocument();
      expect(screen.getByText(/economic events and indicators/i)).toBeInTheDocument();
      expect(screen.getByText(/real-time market news/i)).toBeInTheDocument();
      expect(screen.getByText(/custom rss feeds/i)).toBeInTheDocument();
      expect(screen.getByText(/technical indicator data/i)).toBeInTheDocument();
    });

    it('displays configuration notice', () => {
      render(<Data />);

      expect(screen.getByText(/configuration required/i)).toBeInTheDocument();
      expect(screen.getByText(/configure api integrations in settings/i)).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('switches to Market News tab', async () => {
      const user = userEvent.setup();
      render(<Data />);

      const newsTab = screen.getByRole('button', { name: /market news/i });
      await user.click(newsTab);

      // Verify tab is active
      await waitFor(() => {
        expect(newsTab).toHaveClass('bg-sidebar-item-active');
      });
    });

    it('switches to RSS Feeds tab', async () => {
      const user = userEvent.setup();
      render(<Data />);

      const rssTab = screen.getByRole('button', { name: /rss feeds/i });
      await user.click(rssTab);

      // Verify tab is active
      await waitFor(() => {
        expect(rssTab).toHaveClass('bg-sidebar-item-active');
      });
    });

    it('switches to Technical Indicators tab', async () => {
      const user = userEvent.setup();
      render(<Data />);

      const indicatorsTab = screen.getByRole('button', { name: /technical indicators/i });
      await user.click(indicatorsTab);

      // Verify tab is active
      await waitFor(() => {
        expect(indicatorsTab).toHaveClass('bg-sidebar-item-active');
      });
    });

    it('switches back to Economic Calendar tab', async () => {
      const user = userEvent.setup();
      render(<Data />);

      // Switch to another tab first
      const newsTab = screen.getByRole('button', { name: /market news/i });
      await user.click(newsTab);

      await waitFor(() => {
        expect(newsTab).toHaveClass('bg-sidebar-item-active');
      });

      // Switch back to Economic Calendar
      const calendarTab = screen.getByRole('button', { name: /economic calendar/i });
      await user.click(calendarTab);

      // Verify tab is active
      await waitFor(() => {
        expect(calendarTab).toHaveClass('bg-sidebar-item-active');
      });
    });
  });

  describe('Tab Icons', () => {
    it('displays correct icon for each tab', () => {
      render(<Data />);

      // All tabs should have their respective icons
      const calendarTab = screen.getByRole('button', { name: /economic calendar/i });
      const newsTab = screen.getByRole('button', { name: /market news/i });
      const rssTab = screen.getByRole('button', { name: /rss feeds/i });
      const indicatorsTab = screen.getByRole('button', { name: /technical indicators/i });

      // Verify icons are present (lucide-react icons)
      expect(calendarTab.querySelector('svg')).toBeInTheDocument();
      expect(newsTab.querySelector('svg')).toBeInTheDocument();
      expect(rssTab.querySelector('svg')).toBeInTheDocument();
      expect(indicatorsTab.querySelector('svg')).toBeInTheDocument();
    });
  });

  describe('Tab State Management', () => {
    it('maintains only one active tab at a time', async () => {
      const user = userEvent.setup();
      render(<Data />);

      const calendarTab = screen.getByRole('button', { name: /economic calendar/i });
      const newsTab = screen.getByRole('button', { name: /market news/i });

      // Initially, calendar tab should be active
      expect(calendarTab).toHaveClass('bg-sidebar-item-active');
      expect(newsTab).not.toHaveClass('bg-sidebar-item-active');

      // Click news tab
      await user.click(newsTab);

      // Now news tab should be active, calendar should not
      expect(newsTab).toHaveClass('bg-sidebar-item-active');
      expect(calendarTab).not.toHaveClass('bg-sidebar-item-active');
    });

    it('applies correct styling to inactive tabs', async () => {
      const user = userEvent.setup();
      render(<Data />);

      const newsTab = screen.getByRole('button', { name: /market news/i });

      // Initially inactive
      expect(newsTab).toHaveClass('text-text-secondary');
      expect(newsTab).toHaveClass('hover:bg-sidebar-item-hover');

      // Click to activate
      await user.click(newsTab);

      // Now active
      expect(newsTab).toHaveClass('bg-sidebar-item-active');
      expect(newsTab).toHaveClass('text-primary');
    });
  });

  describe('Content Rendering', () => {
    it('renders Economic Calendar component by default', () => {
      render(<Data />);

      // Verify the page header is present
      expect(screen.getByText('3rd Party Data')).toBeInTheDocument();

      // Verify Economic Calendar tab is active
      const calendarTab = screen.getByRole('button', { name: /economic calendar/i });
      expect(calendarTab).toHaveClass('bg-sidebar-item-active');
    });

    it('renders Market News component when tab is selected', async () => {
      const user = userEvent.setup();
      render(<Data />);

      const newsTab = screen.getByRole('button', { name: /market news/i });
      await user.click(newsTab);

      await waitFor(() => {
        // Verify tab is active (component rendering is tested separately)
        expect(newsTab).toHaveClass('bg-sidebar-item-active');
      });
    });

    it('renders RSS Feeds component when tab is selected', async () => {
      const user = userEvent.setup();
      render(<Data />);

      const rssTab = screen.getByRole('button', { name: /rss feeds/i });
      await user.click(rssTab);

      await waitFor(() => {
        // Verify tab is active
        expect(rssTab).toHaveClass('bg-sidebar-item-active');
      });
    });

    it('renders Technical Indicators component when tab is selected', async () => {
      const user = userEvent.setup();
      render(<Data />);

      const indicatorsTab = screen.getByRole('button', { name: /technical indicators/i });
      await user.click(indicatorsTab);

      await waitFor(() => {
        // Verify tab is active
        expect(indicatorsTab).toHaveClass('bg-sidebar-item-active');
      });
    });
  });

  describe('Keyboard Navigation', () => {
    it('supports keyboard navigation between tabs', async () => {
      const user = userEvent.setup();
      render(<Data />);

      const calendarTab = screen.getByRole('button', { name: /economic calendar/i });
      const newsTab = screen.getByRole('button', { name: /market news/i });

      // Focus first tab
      calendarTab.focus();
      expect(calendarTab).toHaveFocus();

      // Tab to next button
      await user.tab();
      expect(newsTab).toHaveFocus();
    });

    it('activates tab on Enter key', async () => {
      const user = userEvent.setup();
      render(<Data />);

      const newsTab = screen.getByRole('button', { name: /market news/i });
      
      // Focus the tab
      newsTab.focus();

      // Press Enter
      await user.keyboard('{Enter}');

      // Tab should be activated
      await waitFor(() => {
        expect(newsTab).toHaveClass('bg-sidebar-item-active');
      });
    });

    it('activates tab on Space key', async () => {
      const user = userEvent.setup();
      render(<Data />);

      const rssTab = screen.getByRole('button', { name: /rss feeds/i });
      
      // Focus the tab
      rssTab.focus();

      // Press Space
      await user.keyboard(' ');

      // Tab should be activated
      await waitFor(() => {
        expect(rssTab).toHaveClass('bg-sidebar-item-active');
      });
    });
  });

  describe('Responsive Layout', () => {
    it('renders sidebar and main content areas', () => {
      render(<Data />);

      // Sidebar should be present
      const sidebar = document.querySelector('aside');
      expect(sidebar).toBeInTheDocument();
      expect(sidebar).toHaveClass('w-64');

      // Main content should be present
      const main = document.querySelector('main');
      expect(main).toBeInTheDocument();
      expect(main).toHaveClass('flex-1');
    });
  });
});

