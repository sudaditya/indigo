import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router';
import { AknRenderer } from '../components/AknRenderer';
import { apiFetch } from '../api/client';

interface Work {
  id: number;
  title: string;
  numbered_title: string;
  frbr_uri: string;
  publication_date: string;
}

interface DocumentContent {
  content: string;
}

export function DocumentViewer() {
  const { id } = useParams<{ id: string }>();

  const [work, setWork] = useState<Work | null>(null);
  const [xml, setXml] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDocument() {
      if (!id) return;
      try {
        const [workData, contentData] = await Promise.all([
          apiFetch<Work>(`/works/${id}`),
          apiFetch<DocumentContent>(`/documents/${id}/content`),
        ]);
        setWork(workData);
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