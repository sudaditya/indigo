import { Tooltip } from './Tooltip';
/**
 * Renders the FRBR URI of the current work, with the expression date
 * styled as a clickable "time-travel" affordance.
 *
 * Current version: date is visually clickable but does nothing (or shows
 * a "coming soon" hint). Real time-travel requires the amendment engine
 * — deferred to Phase 5.
 *
 * Mockup shows this bar sitting between the document header and the tab
 * strip, always visible while browsing an MD.
 */
interface FrbrUriBarProps {
  frbrUri: string;               // e.g. /akn/in/act/masterDirection/2025-11-28/172
  expressionDate: string;        // ISO date shown as the clickable pill
}

export function FrbrUriBar({ frbrUri, expressionDate }: FrbrUriBarProps) {
  return (
    <div className="frbr-bar">
      <div className="frbr-bar-inner">
        <div className="frbr-bar-label">
          <span>FRBR URI</span>
          <span className="frbr-bar-dot">·</span>
          <span className="frbr-bar-hint">time-travel coming soon</span>
        </div>
        <div className="frbr-bar-uri">
          <span className="frbr-bar-uri-fixed">{frbrUri}</span>
          <span className="frbr-bar-uri-lang">/eng@</span>
        <Tooltip content="Time-travel to a different point-in-time — coming in Phase 5">
          <button
            className="frbr-bar-date"
            disabled
          >
            {expressionDate}
          </button>
          </Tooltip>
          <span className="frbr-bar-uri-fixed">/</span>
        </div>
      </div>
    </div>
  );
}