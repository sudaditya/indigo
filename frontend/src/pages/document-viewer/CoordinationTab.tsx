import { useEffect, useState } from 'react';
import { apiFetch } from '../../api/client';
import type { DraftAmendment, MDOwnership, PaginatedResponse } from '../../api/types';
import { groupDraftsByTarget } from './conflict-detection';
import type { DraftGroup } from './conflict-detection';

interface CoordinationTabProps {
  workId: string;
}

export function CoordinationTab({ workId }: CoordinationTabProps) {
  const [ownership, setOwnership] = useState<MDOwnership | null>(null);
  const [drafts, setDrafts] = useState<DraftAmendment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        // Two parallel fetches:
        // 1) all MDOwnerships — filter client-side (only 3 MDs, cheap)
        //    (Simpler than adding filter support to the backend for now.)
        // 2) drafts filtered to this MD via the ?work= query param
        const [ownershipsData, draftsData] = await Promise.all([
          apiFetch<PaginatedResponse<MDOwnership>>('/rbi/mds/'),
          apiFetch<PaginatedResponse<DraftAmendment>>('/rbi/drafts/', {
            work: workId,
          }),
        ]);

        const own = ownershipsData.results.find(
          (o) => String(o.work.id) === workId
        );
        setOwnership(own || null);
        setDrafts(draftsData.results);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [workId]);

  if (loading) return <div className="tab-placeholder"><p>Loading coordination data…</p></div>;

  if (error) return (
    <div className="error">
      <strong>Could not load coordination data:</strong> {error}
    </div>
  );

  const groups = groupDraftsByTarget(drafts);
  const conflictGroups = groups.filter((g) => g.conflict !== null);
  const nonConflictGroups = groups.filter((g) => g.conflict === null);

  return (
    <div className="coordination-tab">
      {/* Ownership summary */}
      {ownership && (
        <section className="coord-section coord-ownership">
          <div className="coord-ownership-label">Nodal owner</div>
          <div className="coord-ownership-value">
            {ownership.nodal_unit.name}
            <span className="coord-ownership-code">
              {ownership.nodal_unit.short_code} · {ownership.nodal_unit.division_display}
            </span>
          </div>
        </section>
      )}

      {/* Empty state */}
      {drafts.length === 0 && (
        <section className="coord-section coord-empty">
          <p>No active drafts on this Master Direction.</p>
        </section>
      )}

      {/* Conflicts section — surfaced first */}
      {conflictGroups.length > 0 && (
        <section className="coord-section">
          <h3 className="coord-heading">
            Conflicts ({conflictGroups.length})
          </h3>
          <div className="coord-groups">
            {conflictGroups.map((group) => (
              <DraftGroupCard key={group.targetEid} group={group} />
            ))}
          </div>
        </section>
      )}

      {/* Non-conflict drafts — grouped by target */}
      {nonConflictGroups.length > 0 && (
        <section className="coord-section">
          <h3 className="coord-heading">
            Other active drafts ({nonConflictGroups.length})
          </h3>
          <div className="coord-groups">
            {nonConflictGroups.map((group) => (
              <DraftGroupCard key={group.targetEid} group={group} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

/**
 * Card representing all drafts on a single target eId.
 * Shows conflict badge if applicable, then lists each draft.
 */
function DraftGroupCard({ group }: { group: DraftGroup }) {
  const { targetEid, drafts, conflict } = group;

  return (
        <article
      className={
        conflict
          ? conflict.severity === 'high'
            ? 'draft-group draft-group-conflict draft-group-conflict-high'
            : 'draft-group draft-group-conflict'
          : 'draft-group'
      }
    >
      <header className="draft-group-header">
        <span className="draft-group-eid">
          <span className="draft-group-eid-label">Target</span>
          {targetEid}
        </span>
        {conflict && (
          <span className={`conflict-badge conflict-badge-${conflict.severity}`}>
            {conflict.conflictType === 'delete_vs_edit'
              ? 'Delete vs. Edit'
              : `${drafts.length} drafts on same target`}
          </span>
        )}
      </header>

      <div className="draft-list">
        {drafts.map((draft) => (
          <DraftCard key={draft.id} draft={draft} />
        ))}
      </div>
    </article>
  );
}

/**
 * Individual draft card — shows change type, author, status, proposed text.
 */
function DraftCard({ draft }: { draft: DraftAmendment }) {
  return (
    <div className="draft-card">
      <div className="draft-card-header">
        <span className={`change-type change-type-${draft.change_type}`}>
          {draft.change_type_display}
        </span>
        <span className={`status-pill status-${draft.status}`}>
          {draft.status_display}
        </span>
      </div>

      <div className="draft-author">
        <strong>{draft.author_user.full_name}</strong>
        <span className="draft-author-unit">
          {draft.author_unit.short_code} · {draft.author_unit.name}
        </span>
      </div>

      {draft.proposed_text && (
        <div className="draft-proposed-text">
          <div className="draft-label">Proposed text</div>
          <div className="draft-text">{draft.proposed_text}</div>
        </div>
      )}

      {draft.rationale && (
        <div className="draft-rationale">
          <div className="draft-label">Rationale</div>
          <div className="draft-text draft-text-muted">{draft.rationale}</div>
        </div>
      )}

      <div className="draft-footer">
        Created {new Date(draft.created_at).toLocaleDateString()}
      </div>
    </div>
  );
}