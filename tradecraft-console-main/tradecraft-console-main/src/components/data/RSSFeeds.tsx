import React, { useState, useEffect } from 'react';
import { Rss, Plus, Trash2, ExternalLink, RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import {
  getRSSFeeds,
  addRSSFeed,
  deleteRSSFeed,
  getRSSArticles,
  type RSSFeed,
  type RSSArticle,
} from '@/lib/api';

const RSSFeeds: React.FC = () => {
  const [feeds, setFeeds] = useState<RSSFeed[]>([]);
  const [articles, setArticles] = useState<RSSArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFeed, setSelectedFeed] = useState<string | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [newFeedName, setNewFeedName] = useState('');
  const [newFeedUrl, setNewFeedUrl] = useState('');
  const [newFeedCategory, setNewFeedCategory] = useState('');

  useEffect(() => {
    loadFeeds();
  }, []);

  useEffect(() => {
    if (feeds.length > 0) {
      loadArticles();
    }
  }, [selectedFeed]);

  const loadFeeds = async () => {
    try {
      const data = await getRSSFeeds();
      setFeeds(data.feeds);
    } catch (error: any) {
      toast.error(`Failed to load RSS feeds: ${error.message}`);
    }
  };

  const loadArticles = async () => {
    setLoading(true);
    try {
      const data = await getRSSArticles(selectedFeed || undefined, 50);
      setArticles(data.articles);
    } catch (error: any) {
      toast.error(`Failed to load articles: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAddFeed = async () => {
    if (!newFeedName || !newFeedUrl) {
      toast.error('Please enter feed name and URL');
      return;
    }

    try {
      await addRSSFeed(newFeedName, newFeedUrl, newFeedCategory || undefined);
      toast.success('RSS feed added successfully');
      setNewFeedName('');
      setNewFeedUrl('');
      setNewFeedCategory('');
      setShowAddDialog(false);
      await loadFeeds();
    } catch (error: any) {
      toast.error(`Failed to add feed: ${error.message}`);
    }
  };

  const handleDeleteFeed = async (feedId: string, feedName: string) => {
    if (!confirm(`Are you sure you want to remove the feed "${feedName}"?`)) {
      return;
    }

    try {
      await deleteRSSFeed(feedId);
      toast.success('Feed removed successfully');
      if (selectedFeed === feedId) {
        setSelectedFeed(null);
      }
      await loadFeeds();
    } catch (error: any) {
      toast.error(`Failed to remove feed: ${error.message}`);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Rss className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold">RSS Feeds</h2>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={loadArticles} disabled={loading}>
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
          <Button size="sm" onClick={() => setShowAddDialog(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Feed
          </Button>
        </div>
      </div>

      <div className="flex-1 flex gap-4 overflow-hidden">
        {/* Feeds Sidebar */}
        <div className="w-64 flex flex-col">
          <div className="text-xs font-medium text-text-muted mb-2">Feeds ({feeds.length})</div>
          <div className="flex-1 overflow-auto space-y-1">
            <button
              onClick={() => setSelectedFeed(null)}
              className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                selectedFeed === null
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-panel hover:bg-panel-dark text-text-secondary'
              }`}
            >
              All Feeds
            </button>
            {feeds.map((feed) => (
              <div
                key={feed.id}
                className={`flex items-center gap-2 px-3 py-2 rounded transition-colors ${
                  selectedFeed === feed.id
                    ? 'bg-primary/20 border border-primary/50'
                    : 'bg-panel hover:bg-panel-dark border border-transparent'
                }`}
              >
                <button
                  onClick={() => setSelectedFeed(feed.id)}
                  className="flex-1 text-left text-sm text-text-primary"
                >
                  {feed.name}
                </button>
                <button
                  onClick={() => handleDeleteFeed(feed.id, feed.name)}
                  className="p-1 hover:bg-red-500/20 rounded transition-colors"
                >
                  <Trash2 className="w-3 h-3 text-red-500" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Articles */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <RefreshCw className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : articles.length === 0 ? (
            <Alert>
              <AlertCircle className="w-4 h-4" />
              <AlertDescription>
                {feeds.length === 0
                  ? 'No RSS feeds configured. Click "Add Feed" to get started.'
                  : 'No articles found. Try refreshing or check your feed URLs.'}
              </AlertDescription>
            </Alert>
          ) : (
            <div className="flex-1 overflow-auto space-y-3">
              {articles.map((article) => (
                <div
                  key={article.id}
                  className="bg-panel rounded-lg border border-border p-4 hover:border-primary/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs px-2 py-0.5 rounded bg-primary/20 text-primary">
                          {article.feed_name}
                        </span>
                        <span className="text-xs text-text-muted">
                          {formatDate(article.published)}
                        </span>
                      </div>
                      <h3 className="text-sm font-semibold text-text-primary mb-2">
                        {article.title}
                      </h3>
                      {article.summary && (
                        <p className="text-xs text-text-secondary mb-2 line-clamp-2">
                          {article.summary}
                        </p>
                      )}
                    </div>
                  </div>
                  <a
                    href={article.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                  >
                    Read more
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add Feed Dialog */}
      {showAddDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-panel rounded-lg border border-border p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Add RSS Feed</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-text-muted mb-1 block">Feed Name</label>
                <input
                  type="text"
                  value={newFeedName}
                  onChange={(e) => setNewFeedName(e.target.value)}
                  placeholder="e.g., Financial Times"
                  className="w-full px-3 py-2 text-sm bg-background border border-border rounded"
                />
              </div>
              <div>
                <label className="text-sm text-text-muted mb-1 block">Feed URL</label>
                <input
                  type="url"
                  value={newFeedUrl}
                  onChange={(e) => setNewFeedUrl(e.target.value)}
                  placeholder="https://example.com/feed.xml"
                  className="w-full px-3 py-2 text-sm bg-background border border-border rounded"
                />
              </div>
              <div>
                <label className="text-sm text-text-muted mb-1 block">Category (Optional)</label>
                <input
                  type="text"
                  value={newFeedCategory}
                  onChange={(e) => setNewFeedCategory(e.target.value)}
                  placeholder="e.g., Finance, Technology"
                  className="w-full px-3 py-2 text-sm bg-background border border-border rounded"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <Button variant="outline" onClick={() => setShowAddDialog(false)} className="flex-1">
                Cancel
              </Button>
              <Button onClick={handleAddFeed} className="flex-1">
                Add Feed
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RSSFeeds;

