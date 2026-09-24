/**
 * AknRenderer — parses AKN 3.0 XML and renders it as HTML.
 *
 * Design: recursive traversal of the XML DOM tree. For each AKN element
 * we care about, we produce corresponding HTML. Elements we don't handle
 * fall through to a generic renderer that shows their text content.
 *
 * Selection support (Session 13):
 * - When onSelect prop is provided, paragraphs and subparagraphs become
 *   clickable. Clicking one calls onSelect with the eid + node type +
 *   plain-text content.
 * - selectedEid prop highlights the currently-selected node.
 * - Structural containers (chapter, section) are NOT selectable in this
 *   pass — users typically select the content within, not the wrapper.
 *
 * Covered elements:
 *  - chapter, section, paragraph, subparagraph (structural)
 *  - num, heading (labels)
 *  - intro, content, p (containers)
 *  - table, tr, th, td (tables)
 *  - preface (front matter)
 */

// The AKN namespace — all elements are prefixed with this in the XML.
const AKN_NS = 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0';

interface AknRendererProps {
  xml: string;
  /**
   * Called when the user clicks a selectable node (paragraph or subparagraph).
   * If omitted, nodes render as static content — clicks do nothing.
   */
  onSelect?: (selection: SelectedProvision) => void;
  /**
   * eId of the currently-selected node, for highlight styling.
   */
  selectedEid?: string | null;
}

/**
 * Info about a selected provision, captured on click.
 * We include text so the parent can pre-populate the editor without
 * re-fetching / re-parsing.
 */
export interface SelectedProvision {
  eid: string;
  nodeType: 'paragraph' | 'subparagraph';
  /** Human-readable label like "6." or "(ii)" — from the <num> child */
  num: string | null;
  /** Plain-text content of the provision (from any nested <p> tags) */
  text: string;
}

/**
 * Extract the direct text content of a node, skipping child elements.
 * Used to get the value of <num> and <heading> tags cleanly.
 */
function getDirectText(node: Element): string {
  let text = '';
  for (const child of Array.from(node.childNodes)) {
    if (child.nodeType === Node.TEXT_NODE) {
      text += child.textContent || '';
    }
  }
  return text.trim();
}

export function AknRenderer({ xml, onSelect, selectedEid }: AknRendererProps) {
  // Parse the XML string into a DOM tree
  const parser = new DOMParser();
  const doc = parser.parseFromString(xml, 'application/xml');

  // Check for XML parse errors — DOMParser produces a specific <parsererror> element
  const parseError = doc.getElementsByTagName('parsererror')[0];
  if (parseError) {
    return (
      <div className="error">
        <strong>Could not parse document XML.</strong>
        <pre>{parseError.textContent}</pre>
      </div>
    );
  }

  // Find the root <akomaNtoso> element, then descend to <act>
  const act = doc.getElementsByTagNameNS(AKN_NS, 'act')[0];
  if (!act) {
    return <div className="error">No &lt;act&gt; element found in document.</div>;
  }

  /**
   * Extract the plain-text content of a paragraph/subparagraph, walking
   * into <intro>, <content>, and <p> children but skipping <num>/<heading>.
   * Used to seed the editor with the provision's current text.
   */
  function extractProvisionText(el: Element): string {
    const parts: string[] = [];
    for (const child of Array.from(el.children)) {
      const tag = child.localName;
      if (tag === 'num' || tag === 'heading') continue;
      if (tag === 'p') {
        parts.push(child.textContent?.trim() || '');
      } else {
        parts.push(extractProvisionText(child));
      }
    }
    return parts.join(' ').replace(/\s+/g, ' ').trim();
  }

  /**
   * The recursive renderer. Nested inside AknRenderer so it can close over
   * the onSelect / selectedEid props without prop drilling.
   */
  function renderElement(el: Element, key: string): React.ReactNode {
    const tag = el.localName;

    // Extract <num> and <heading> children if present — these appear as
    // labels on structural elements (Chapter I, Section A, etc.)
    const numEl = el.getElementsByTagNameNS(AKN_NS, 'num')[0];
    const headingEl = el.getElementsByTagNameNS(AKN_NS, 'heading')[0];
    // Only use them if they're DIRECT children (not from nested elements)
    const num = numEl?.parentElement === el ? getDirectText(numEl) : null;
    const heading = headingEl?.parentElement === el ? getDirectText(headingEl) : null;

    // Recursively render children, skipping <num> and <heading> (we handle them above)
    const children = Array.from(el.children)
      .filter(child => child.localName !== 'num' && child.localName !== 'heading')
      .map((child, i) => renderElement(child, `${key}-${i}`));

    // Selection handlers — active only when onSelect is provided AND
    // the element is a leaf-ish content node (paragraph or subparagraph).
    const eid = el.getAttribute('eId');
    const isSelectable = Boolean(
      onSelect && (tag === 'paragraph' || tag === 'subparagraph') && eid
    );
    const isSelected = Boolean(eid && eid === selectedEid);

    const handleClick = isSelectable
      ? (e: React.MouseEvent) => {
          // Stop event from bubbling to the parent paragraph, so clicking
          // a subparagraph selects only the subparagraph.
          e.stopPropagation();
          onSelect!({
            eid: eid!,
            nodeType: tag as 'paragraph' | 'subparagraph',
            num,
            text: extractProvisionText(el),
          });
        }
      : undefined;

    switch (tag) {
      case 'preface':
        return (
          <div key={key} className="akn-preface">
            {children}
          </div>
        );

      case 'chapter':
        return (
          <section key={key} className="akn-chapter">
            <h2 className="akn-chapter-header">
              {num && <span className="akn-num">Chapter {num}</span>}
              {heading && (
                <>
                  <span className="akn-heading-separator"> - </span>
                  <span className="akn-heading">{heading}</span>
                </>
              )}
            </h2>
            {children}
          </section>
        );

      case 'section':
        return (
          <section key={key} className="akn-section">
            <h3 className="akn-section-header">
              {num && <span className="akn-num">{num}</span>}
              {heading && <span className="akn-heading">{heading}</span>}
            </h3>
            {children}
          </section>
        );

      case 'paragraph':
        return (
          <div
            key={key}
            className={
              isSelectable
                ? `akn-paragraph akn-selectable ${isSelected ? 'akn-selected' : ''}`
                : 'akn-paragraph'
            }
            onClick={handleClick}
          >
            {num && <span className="akn-para-num">{num}</span>}
            <div className="akn-para-body">{children}</div>
          </div>
        );

      case 'subparagraph':
        return (
          <div
            key={key}
            className={
              isSelectable
                ? `akn-subparagraph akn-selectable ${isSelected ? 'akn-selected' : ''}`
                : 'akn-subparagraph'
            }
            onClick={handleClick}
          >
            {num && <span className="akn-subpara-num">{num}</span>}
            <div className="akn-subpara-body">{children}</div>
          </div>
        );

      case 'intro':
      case 'content':
        // These are containers — no special styling, just render children
        return <div key={key} className={`akn-${tag}`}>{children}</div>;

      case 'p':
        // Actual paragraph text
        return <p key={key}>{el.textContent}</p>;

      case 'table':
        return <table key={key} className="akn-table">{children}</table>;

      case 'tr':
        return <tr key={key}>{children}</tr>;

      case 'th':
        return (
          <th key={key} colSpan={parseInt(el.getAttribute('colspan') || '1')}>
            {el.textContent}
          </th>
        );

      case 'td':
        return (
          <td key={key} colSpan={parseInt(el.getAttribute('colspan') || '1')}>
            {children.length > 0 ? children : el.textContent}
          </td>
        );

      default:
        // Unknown element — render its children if any, or its text
        if (el.children.length > 0) {
          return <div key={key} className={`akn-${tag}`}>{children}</div>;
        }
        return el.textContent ? <span key={key}>{el.textContent}</span> : null;
    }
  }

  // Render the preface and body sections
  const preface = act.getElementsByTagNameNS(AKN_NS, 'preface')[0];
  const body = act.getElementsByTagNameNS(AKN_NS, 'body')[0];

  return (
    <article className="akn-document">
      {preface && renderElement(preface, 'preface')}
      {body && (
        <div className="akn-body">
          {Array.from(body.children).map((child, i) =>
            renderElement(child, `body-${i}`)
          )}
        </div>
      )}
    </article>
  );
}