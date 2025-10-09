import React, { useState } from 'react';
import { Database, Calendar, Newspaper, Rss, TrendingUp } from 'lucide-react';
import EconomicCalendar from '@/components/data/EconomicCalendar';
import MarketNews from '@/components/data/MarketNews';
import RSSFeeds from '@/components/data/RSSFeeds';
import TechnicalIndicators from '@/components/data/TechnicalIndicators';

type TabType = 'CALENDAR' | 'NEWS' | 'RSS' | 'INDICATORS';

const Data: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('CALENDAR');

  const tabs = [
    { id: 'CALENDAR' as TabType, label: 'Economic Calendar', icon: Calendar },
    { id: 'NEWS' as TabType, label: 'Market News', icon: Newspaper },
    { id: 'RSS' as TabType, label: 'RSS Feeds', icon: Rss },
    { id: 'INDICATORS' as TabType, label: 'Technical Indicators', icon: TrendingUp },
  ];

  return (
    <div className="min-h-screen bg-background text-text-primary">
      {/* Header */}
      <div className="h-header bg-panel border-b border-border flex items-center px-4">
        <div className="flex items-center gap-3">
          <Database className="w-6 h-6 text-primary" />
          <h1 className="text-lg font-semibold">3rd Party Data</h1>
        </div>
      </div>

      {/* Content */}
      <div className="flex h-[calc(100vh-3.5rem)]">
        {/* Tabs Sidebar */}
        <aside className="w-64 bg-sidebar border-r border-sidebar-border p-3">
          <div className="space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'bg-sidebar-item-active text-primary font-medium'
                      : 'text-text-secondary hover:bg-sidebar-item-hover'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Info Section */}
          <div className="mt-6 p-3 bg-panel-dark rounded-lg border border-border">
            <div className="text-xs text-text-muted mb-2">About 3rd Party Data</div>
            <div className="text-xs text-text-secondary space-y-2">
              <p>
                Access external data sources to enhance your trading analysis:
              </p>
              <ul className="list-disc list-inside space-y-1">
                <li>Economic events and indicators</li>
                <li>Real-time market news</li>
                <li>Custom RSS feeds</li>
                <li>Technical indicator data</li>
              </ul>
            </div>
          </div>

          {/* Configuration Notice */}
          <div className="mt-4 p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
            <div className="text-xs text-yellow-500 mb-1 font-medium">Configuration Required</div>
            <div className="text-xs text-text-secondary">
              Configure API integrations in Settings to enable Economic Calendar and Market News features.
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden">
          <div className="h-full p-6">
            {activeTab === 'CALENDAR' && <EconomicCalendar />}
            {activeTab === 'NEWS' && <MarketNews />}
            {activeTab === 'RSS' && <RSSFeeds />}
            {activeTab === 'INDICATORS' && <TechnicalIndicators />}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Data;

