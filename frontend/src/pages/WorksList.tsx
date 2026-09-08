import { useEffect, useState } from 'react';
import { Link } from 'react-router';

interface Work {
  id: number;
  title: string;
  numbered_title: string;
  publication_name: string;
  publication_number: string;
  publication_date: string;
  frbr_uri: string;
  principal: boolean;
  stub: boolean;
}

interface WorksResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Work[];
}

const API_BASE = 'http://localhost:8000/api';
const API_TOKEN = 'c6f1cada6b327ee801ee6bac77e0c94b5ceb019c';

export function WorksList() {
  const [works, setWorks] = useState<Work[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchWorks() {
      try {
        const response = await fetch(`${API_BASE}/works`, {
          headers: {
            'Authorization': `Token ${API_TOKEN}`,
            'Accept': 'application/json',
          },
        });
        if (!response.ok) throw new Error(`API returned ${response.status}: ${response.statusText}`);
        const data: WorksResponse = await response.json();
        setWorks(data.results);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    }
    fetchWorks();
  }, []);

  if (loading) return <div className="app"><h1>RBI Master Directions Registry</h1><p>Loading...</p></div>;

  if (error) return (
    <div className="app">
      <h1>RBI Master Directions Registry</h1>
      <div className="error">
        <strong>Error loading data:</strong> {error}
      </div>
    </div>
  );

  return (
    <div className="app">
      <h1>RBI Master Directions Registry</h1>
      <p className="subtitle">{works.length} Master Direction{works.length !== 1 ? 's' : ''} loaded</p>

      <ul className="works-list">
        {works.map((work) => (
          <li key={work.id} className="work-card">
            {/* Each card is now a link to the document viewer */}
            <Link to={`/works/${work.id}`} className="work-card-link">
              <div className="work-header">
                <span className="work-number">{work.numbered_title}</span>
                {work.principal && <span className="badge badge-principal">Principal</span>}
                {work.stub && <span className="badge badge-stub">Stub</span>}
              </div>
              <h2 className="work-title">{work.title}</h2>
              <div className="work-meta">
                <span>Published: {work.publication_date}</span>
                <span className="work-uri">{work.frbr_uri}</span>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}