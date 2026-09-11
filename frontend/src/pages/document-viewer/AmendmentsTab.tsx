import { useState } from 'react';
import { TipTapEditor } from '../../components/TipTapEditor';

/**
 * Placeholder amendments tab — for now, just a scratchpad TipTap editor
 * that proves the editor works. Real amendment workflow comes in Step 3-4.
 */
export function AmendmentsTab() {
  const [content, setContent] = useState('');

  return (
    <div className="amendments-tab">
      <div className="amendments-scratchpad-intro">
        <h3>Amendment editor — scratchpad</h3>
        <p>
          Temporary space to verify the TipTap editor is working. Type below;
          the current HTML will appear underneath.
        </p>
      </div>

      <TipTapEditor
        initialContent="<p>Try typing here. Try <strong>bold</strong> (Cmd+B) and <em>italic</em> (Cmd+I).</p>"
        onChange={setContent}
      />

      <details className="scratchpad-output">
        <summary>Current editor HTML (click to expand)</summary>
        <pre>{content || '(no changes yet)'}</pre>
      </details>
    </div>
  );
}