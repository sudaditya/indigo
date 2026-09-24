import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { apiFetch } from '../api/client';
import type { MDOwnership, PaginatedResponse } from '../api/types';
import { UploadMDModal } from '../components/UploadMDModal';

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

/**
 * Enriched view: Work + its coordination stats (from MDOwnership).
 * Not every Work has an MDOwnership yet, so ownership is optional.
 */
interface EnrichedWork extends Work {
  ownership: MDOwnership | null;
}

export function WorksList() {
  const [works, setWorks] = useState<EnrichedWork[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Upload modal state
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadSuccessMessage, setUploadSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAll() {
      try {
        // Fetch both in parallel — works list from Indigo, ownership from our app
        const [worksData, ownershipData] = await Promise.all([
          apiFetch<WorksResponse>('/works'),
          apiFetch<PaginatedResponse<MDOwnership>>('/rbi/mds/'),
        ]);

        // Join: for each Work, find its ownership record (if any).
        // Small N so a linear find is fine — no need for a Map.
        const enriched: EnrichedWork[] = worksData.results.map((w) => ({
          ...w,
          ownership: ownershipData.results.find((o) => o.work.id === w.id) || null,
        }));

        setWorks(enriched);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
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
      <div className="works-header">
        <div>
          <h1>RBI Master Directions Registry</h1>
          <p className="subtitle">
            {works.length} Master Direction{works.length !== 1 ? 's' : ''} loaded
          </p>
        </div>
        <button
          className="btn btn-primary btn-upload"
          onClick={() => setUploadModalOpen(true)}
        >
          + Upload MD
        </button>
      </div>

      {uploadSuccessMessage && (
        <div
          className="save-toast"
          style={{ position: 'relative', top: 0, right: 0, marginBottom: '1rem' }}
        >
          <span>✓ {uploadSuccessMessage}</span>
          <button
            className="save-toast-close"
            onClick={() => setUploadSuccessMessage(null)}
            aria-label="Dismiss"
          >
            ×
          </button>
        </div>
      )}

      <UploadMDModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onSuccess={(uploaded) => {
          setUploadSuccessMessage(
            `Uploaded ${uploaded.numbered_title}. Redirecting…`
          );
          setTimeout(() => setUploadSuccessMessage(null), 5000);
        }}
      />

      <ul className="works-list">
        {works.map((work) => (
          <li key={work.id} className="work-card">
            <Link to={`/works/${work.id}/content`} className="work-card-link">
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

              {/* Coordination indicators — only shown for MDs with ownership records */}
              {work.ownership && (
                <div className="work-coordination">
                  <span className="work-nodal">
                    Nodal: <strong>{work.ownership.nodal_unit.short_code}</strong>
                  </span>
                  <span className="work-drafts">
                    {work.ownership.draft_count} draft{work.ownership.draft_count !== 1 ? 's' : ''}
                  </span>
                  {work.ownership.conflict_count > 0 && (
                    <span className="work-conflicts">
                      ⚠ {work.ownership.conflict_count} conflict{work.ownership.conflict_count !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              )}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}