/**
 * TypeScript types matching our Django REST responses.
 * Keep in sync with serializers.py on the backend.
 */

export interface WorkBrief {
  id: number;
  frbr_uri: string;
  numbered_title: string;
  title: string;
  publication_date: string;
}

export interface UserBrief {
  id: number;
  username: string;
  full_name: string;
}

export interface WorkingUnit {
  id: number;
  name: string;
  short_code: string;
  division: 'PRD' | 'COD';
  division_display: string;
  group_name: string;
  is_group_level: boolean;
}

export interface MDOwnership {
  id: number;
  work: WorkBrief;
  nodal_unit: WorkingUnit;
  edit_restricted: boolean;
  draft_count: number;
  conflict_count: number;
  created_at: string;
  updated_at: string;
}

export type ChangeType = 'insert' | 'modify' | 'delete' | 'renumber';
export type DraftStatus = 'draft' | 'in_review' | 'approved' | 'rejected' | 'withdrawn';

export interface DraftAmendment {
  id: number;
  work: WorkBrief;
  target_eid: string;
  change_type: ChangeType;
  change_type_display: string;
  proposed_text: string;
  rationale: string;
  status: DraftStatus;
  status_display: string;
  author_user: UserBrief;
  author_unit: WorkingUnit;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
}

/**
 * Standard DRF paginated response shape.
 * Our lists come back like { count, next, previous, results: [...] }.
 */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
/**
 * Bundled view of a user + their primary working unit, for the
 * "Viewing as" persona-switching dropdown. Returned by /api/rbi/personas/.
 */
export interface Persona {
  user_id: number;
  username: string;
  full_name: string;
  unit_id: number;
  unit_name: string;
  unit_short_code: string;
  division: 'PRD' | 'COD';
  division_display: string;
}

export interface PersonasResponse {
  personas: Persona[];
}