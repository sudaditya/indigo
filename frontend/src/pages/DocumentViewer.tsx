import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router';
import { AknRenderer } from '../components/AknRenderer';

interface Work {
  id: number;
  title: string;
  numbered_title: string;
  frbr_uri: string;
  publication_date: string;
}

const API_BASE = 'http://localhost:8000/api';
const API_TOKEN = 'c6f1cada6b327ee801ee6bac77e0c94b5ceb019c';

export function DocumentViewer() {
  // useParams reads :id from the URL — /works/3 gives us { id: "3" }
  const { id } = useParams<{ id: string }>();

  const [work, setWork] = useState<Work | null>(null);
  const [xml, setXml] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDocument() {
      if (!id) return;
      try {
        // Two parallel fetches: work metadata AND document XML content
        // Promise.all runs them concurrently, faster than sequential
        const [workRes, contentRes] = await Promise.all([
          fetch(`${API_BASE}/works/${id}`, {
            headers: { 'Authorization': `Token ${API_TOKEN}`, 'Accept': 'application/json' },
          }),
          // Get the associated document's XML. Since a Work has one active Document,
          // we look it up via the documents endpoint filtered by work URI.
          fetch(`${API_BASE}/documents/${id}/content`, {
            headers: { 'Authorization': `Token ${API_TOKEN}`, 'Accept': 'application/json' },
          }),
        ]);

        if (!workRes.ok) throw new Error(`Work fetch failed: ${workRes.status}`);
        if (!contentRes.ok) throw new Error(`Content fetch failed: ${contentRes.status}`);

        const workData: Work = await workRes.json();
        const contentData = await contentRes.json();

        setWork(workData);
        // The content endpoint returns { content: "<akn xml>" }
        setXml(contentData.content);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    }
    fetchDocument();
  }, [id]);

  if (loading) return <div className="app"><p>Loading document...</p></div>;

  if (error) return (
    <div className="app">
      <Link to="/">← Back to Works</Link>
      <div className="error"><strong>Error:</strong> {error}</div>
    </div>
  );

  return (
    <div className="app document-view">
      <Link to="/" className="back-link">← Back to Works</Link>

      <header className="document-header">
        <div className="doc-number">{work?.numbered_title}</div>
        <h1 className="doc-title">{work?.title}</h1>
        <div className="doc-meta">
          Published {work?.publication_date} · <span className="work-uri">{work?.frbr_uri}</span>
        </div>
      </header>

      <div className="document-body">
        {xml && <AknRenderer xml={xml} />}
      </div>
    </div>
  );
}