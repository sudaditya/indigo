/**
 * Renders the top-of-document masthead that appears above the preface.
 * Matches the mockup's convention: centered small-caps issuer, reference
 * codes, title, and "rendered as of" line.
 *
 * Extracts info from the AKN XML rather than requiring separate props —
 * everything we need lives in the FRBR meta or the doc itself.
 */
const AKN_NS = 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0';

interface DocumentMastheadProps {
  xml: string | null;
}

function extractMeta(xml: string) {
  const doc = new DOMParser().parseFromString(xml, 'application/xml');
  const uriEl = doc.getElementsByTagNameNS(AKN_NS, 'FRBRuri')[0];
  const dateEl = doc.getElementsByTagNameNS(AKN_NS, 'FRBRdate')[0];
  const aliasEl = doc.getElementsByTagNameNS(AKN_NS, 'FRBRalias')[0];
  const numberEl = doc.getElementsByTagNameNS(AKN_NS, 'FRBRnumber')[0];

  return {
    frbrUri: uriEl?.getAttribute('value') || '',
    date: dateEl?.getAttribute('date') || '',
    title: aliasEl?.getAttribute('value') || '',
    number: numberEl?.getAttribute('value') || '',
  };
}

function formatLongDate(iso: string): string {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  const months = ['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];
  return `${parseInt(d)} ${months[parseInt(m) - 1]} ${y}`;
}

export function DocumentMasthead({ xml }: DocumentMastheadProps) {
  if (!xml) return null;
  const meta = extractMeta(xml);

  return (
    <header className="doc-masthead">
      <div className="doc-masthead-issuer">Reserve Bank of India</div>
      <div className="doc-masthead-refs">
        Master Direction {meta.number} of {meta.date?.slice(0, 4)}
      </div>
      <h1 className="doc-masthead-title">{meta.title}</h1>
      <div className="doc-masthead-rendered">
        Rendered as of {formatLongDate(meta.date)}
      </div>
    </header>
  );
}