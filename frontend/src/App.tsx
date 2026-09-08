import { useEffect, useState } from 'react';
import './App.css';

// Type definition matching what /api/works returns for each Work.
// TypeScript uses this to catch mistakes as we access fields.
// Fields we don't use yet are omitted — we can add more later.
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

// The API returns a paginated response with count + results array
interface WorksResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Work[];
}

// Django API config — will move to a proper config file later
const API_BASE = 'http://localhost:8000/api';
const API_TOKEN = 'c6f1cada6b327ee801ee6bac77e0c94b5ceb019c';

function App() {
  // Three pieces of state:
  // - works: the list of MDs (empty array until data loads)
  // - loading: true while the fetch is in flight
  // - error: any error message from the API
  const [works, setWorks] = useState<Work[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // useEffect runs once after the component mounts (empty dependency array [])
  // This is where we do the initial data fetch
  useEffect(() => {
    async function fetchWorks() {
      try {
        const response = await fetch(`${API_BASE}/works`, {
          headers: {
            'Authorization': `Token ${API_TOKEN}`,
            'Accept': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }

        const data: WorksResponse = await response.json();
        setWorks(data.results);
      } catch (err) {
        // TypeScript wants us to handle the "err could be anything" case
        const message = err instanceof Error ? err.message : String(err);
        setError(message);
      } finally {
        setLoading(false);
      }
    }

    fetchWorks();
  }, []);

  // Render logic — three states to handle
  if (loading) {
    return (
      <div className="app">
        <h1>RBI Master Directions Registry</h1>
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <h1>RBI Master Directions Registry</h1>
        <div className="error">
          <strong>Error loading data:</strong> {error}
          <p>Check that Docker is running and the API is accessible.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <h1>RBI Master Directions Registry</h1>
      <p className="subtitle">{works.length} Master Direction{works.length !== 1 ? 's' : ''} loaded</p>

      <ul className="works-list">
        {works.map((work) => (
          <li key={work.id} className="work-card">
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
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;