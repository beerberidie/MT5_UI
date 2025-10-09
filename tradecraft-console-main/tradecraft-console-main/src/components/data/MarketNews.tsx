import React, { useState, useEffect } from 'react';
import { Newspaper, Search, RefreshCw, ExternalLink, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import { getNews, type NewsArticle } from '@/lib/api';

const MarketNews: React.FC = () => {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('business');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const categories = [
    { value: 'business', label: 'Business' },
    { value: 'forex', label: 'Forex' },
    { value: 'crypto', label: 'Crypto' },
    { value: 'general', label: 'General' },
    { value: 'technology', label: 'Technology' },
  ];

  useEffect(() => {
    loadNews();
  }, [category, page]);

  const loadNews = async () => {
    setLoading(true);
    try {
      const params: any = {
        category,
        page,
        page_size: pageSize,
      };

      if (searchQuery) {
        params.query = searchQuery;
      }

      const data = await getNews(params);
      setArticles(data.articles);
      setTotal(data.total);
    } catch (error: any) {
      toast.error(`Failed to load news: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    loadNews();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
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

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Newspaper className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold">Market News</h2>
        </div>
        <Button variant="outline" size="sm" onClick={loadNews} disabled={loading}>
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Filters */}
      <div className="bg-panel rounded-lg border border-border p-4 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div>
            <label className="text-xs text-text-muted mb-1 block">Search</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Search news..."
                className="flex-1 px-3 py-2 text-sm bg-background border border-border rounded"
              />
              <Button size="sm" onClick={handleSearch}>
                <Search className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Category */}
          <div>
            <label className="text-xs text-text-muted mb-1 block">Category</label>
            <div className="flex flex-wrap gap-1">
              {categories.map((cat) => (
                <button
                  key={cat.value}
                  onClick={() => {
                    setCategory(cat.value);
                    setPage(1);
                  }}
                  className={`px-3 py-2 text-xs rounded transition-colors ${
                    category === cat.value
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-panel-alt text-text-secondary hover:bg-panel-dark'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Articles List */}
      <div className="flex-1 overflow-auto">
        {loading && articles.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : articles.length === 0 ? (
          <Alert>
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              No news articles found. Try adjusting your search or category filter.
            </AlertDescription>
          </Alert>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {articles.map((article) => (
              <div
                key={article.id}
                className="bg-panel rounded-lg border border-border overflow-hidden hover:border-primary/50 transition-colors"
              >
                {article.image_url && (
                  <div className="aspect-video bg-panel-dark overflow-hidden">
                    <img
                      src={article.image_url}
                      alt={article.title}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  </div>
                )}
                <div className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs text-text-muted">{article.source}</span>
                    <span className="text-xs text-text-muted">•</span>
                    <span className="text-xs text-text-muted">
                      {formatDate(article.published_at)}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-text-primary mb-2 line-clamp-2">
                    {article.title}
                  </h3>
                  {article.description && (
                    <p className="text-xs text-text-secondary mb-3 line-clamp-3">
                      {article.description}
                    </p>
                  )}
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                  >
                    Read more
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {articles.length > 0 && totalPages > 1 && (
        <div className="mt-4 pt-4 border-t border-border flex items-center justify-between">
          <div className="text-xs text-text-muted">
            Page {page} of {totalPages} ({total} total articles)
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1 || loading}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages || loading}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketNews;

