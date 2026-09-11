/**
 * Client-side conflict detection for drafts on a single MD.
 * Mirrors the backend logic in views.ConflictsView but scoped to one MD.
 *
 * Two conflict types:
 *   - same_target: multiple active drafts on the same target_eid
 *   - delete_vs_edit: a DELETE draft + any non-DELETE draft on the same target
 *     (higher severity — a delete makes the other draft moot)
 */
import type { DraftAmendment } from '../../api/types';

export type ConflictType = 'same_target' | 'delete_vs_edit';
export type ConflictSeverity = 'high' | 'medium';

export interface Conflict {
  targetEid: string;
  conflictType: ConflictType;
  severity: ConflictSeverity;
  drafts: DraftAmendment[];
}

/**
 * Group drafts by target_eid and identify conflicts.
 * Returns a Map keyed by target_eid; each value describes drafts on that eId
 * and (if there's more than one active draft) the conflict info.
 */
export interface DraftGroup {
  targetEid: string;
  drafts: DraftAmendment[];
  conflict: Conflict | null;
}

const INACTIVE_STATUSES = new Set(['withdrawn', 'rejected']);

export function groupDraftsByTarget(drafts: DraftAmendment[]): DraftGroup[] {
  // Only active drafts count toward conflicts
  const active = drafts.filter((d) => !INACTIVE_STATUSES.has(d.status));

  // Group by target_eid
  const byTarget = new Map<string, DraftAmendment[]>();
  for (const draft of active) {
    if (!byTarget.has(draft.target_eid)) byTarget.set(draft.target_eid, []);
    byTarget.get(draft.target_eid)!.push(draft);
  }

  // Convert to array of DraftGroup, with conflict info where applicable
  const groups: DraftGroup[] = [];
  for (const [targetEid, groupDrafts] of byTarget.entries()) {
    let conflict: Conflict | null = null;

    if (groupDrafts.length >= 2) {
      const changeTypes = new Set(groupDrafts.map((d) => d.change_type));
      const hasDelete = changeTypes.has('delete');
      const hasNonDelete = changeTypes.size > (hasDelete ? 1 : 0);

      if (hasDelete && hasNonDelete) {
        conflict = {
          targetEid,
          conflictType: 'delete_vs_edit',
          severity: 'high',
          drafts: groupDrafts,
        };
      } else {
        conflict = {
          targetEid,
          conflictType: 'same_target',
          severity: 'medium',
          drafts: groupDrafts,
        };
      }
    }

    groups.push({ targetEid, drafts: groupDrafts, conflict });
  }

  // Sort: conflicts first (by severity), then non-conflict groups
  groups.sort((a, b) => {
    if (a.conflict && !b.conflict) return -1;
    if (!a.conflict && b.conflict) return 1;
    if (a.conflict && b.conflict) {
      const sevOrder = { high: 0, medium: 1 };
      return sevOrder[a.conflict.severity] - sevOrder[b.conflict.severity];
    }
    return a.targetEid.localeCompare(b.targetEid);
  });

  return groups;
}