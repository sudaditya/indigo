import { AknRenderer } from '../../components/AknRenderer';

interface ContentTabProps {
  xml: string | null;
}

/**
 * The "Content" tab of the MD viewer — renders the AKN XML as legal text.
 * This is what the original DocumentViewer showed as its only view.
 */
export function ContentTab({ xml }: ContentTabProps) {
  if (!xml) return <p>No content loaded.</p>;
  return (
    <div className="document-body">
      <AknRenderer xml={xml} />
    </div>
  );
}