/**
 * AknRenderer — parses AKN 3.0 XML and renders it as HTML.
 *
 * Design: recursive traversal of the XML DOM tree. For each AKN element
 * we care about, we produce corresponding HTML. Elements we don't handle
 * fall through to a generic renderer that shows their text content.
 *
 * This is a first-draft renderer for our 3 pilot MDs. It covers:
 *  - chapter, section, paragraph, subparagraph (structural)
 *  - num, heading (labels)
 *  - intro, content, p (containers)
 *  - table, tr, th, td (tables)
 *  - preface (front matter)
 *
 * Elements to add as we encounter them: quote, ref, remark, note, ...
 */

interface AknRendererProps {
  xml: string;
}

// The AKN namespace — all elements are prefixed with this in the XML.
// We use it when querying the DOM to find elements by tag name.
const AKN_NS = 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0';

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

/**
 * The recursive renderer. Given an XML element, return a React element.
 * Uses element.localName (namespace-stripped tag name) to decide how to render.
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
            {num && <span className="akn-num">{num}</span>}
            {heading && <span className="akn-heading">{heading}</span>}
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
        <div key={key} className="akn-paragraph">
          {num && <span className="akn-para-num">{num}</span>}
          <div className="akn-para-body">{children}</div>
        </div>
      );

    case 'subparagraph':
      return (
        <div key={key} className="akn-subparagraph">
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
      return <th key={key} colSpan={parseInt(el.getAttribute('colspan') || '1')}>
        {el.textContent}
      </th>;

    case 'td':
      return <td key={key} colSpan={parseInt(el.getAttribute('colspan') || '1')}>
        {children.length > 0 ? children : el.textContent}
      </td>;

    default:
      // Unknown element — render its children if any, or its text
      if (el.children.length > 0) {
        return <div key={key} className={`akn-${tag}`}>{children}</div>;
      }
      return el.textContent ? <span key={key}>{el.textContent}</span> : null;
  }
}

export function AknRenderer({ xml }: AknRendererProps) {
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