import { useState } from 'react';
import { useParams } from 'react-router';
import { AknRenderer } from '../../components/AknRenderer';
import type { SelectedProvision } from '../../components/AknRenderer';
import { TipTapEditor } from '../../components/TipTapEditor';
import { Modal } from '../../components/Modal';
import { usePersona } from '../../context/PersonaContext';
import { apiPost } from '../../api/client';
import type { DraftAmendmentCreate, DraftAmendment } from '../../api/types';
import { DocumentMasthead } from './DocumentMasthead';

interface ContentTabProps {
  xml: string | null;
}

/**
 * Content tab with selection + editor + save flow.
 *
 * Flow:
 *   1. User clicks a paragraph/subparagraph → captured as `selected`
 *   2. Clicks "Edit this provision" → modal opens, editor pre-populated
 *   3. User edits the text; save button enables once dirty
 *   4. Click Save → POST /api/rbi/drafts/ with current persona as author
 *   5. On success: modal closes, brief confirmation shown, page refresh
 *      forces Coordination tab to re-fetch on next visit
 */
export function ContentTab({ xml }: ContentTabProps) {
  const { id: workIdStr } = useParams<{ id: string }>();
  const workId = workIdStr ? parseInt(workIdStr, 10) : null;

  const [selected, setSelected] = useState<SelectedProvision | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editedHtml, setEditedHtml] = useState('');
  const [originalText, setOriginalText] = useState('');
  const [rationale, setRationale] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [savedConfirmation, setSavedConfirmation] = useState<string | null>(null);

  const { currentPersona } = usePersona();

  if (!xml) return <p>No content loaded.</p>;

  function handleOpenEditor() {
    if (!selected) return;
    const initialHtml = `<p>${escapeHtml(selected.text)}</p>`;
    setEditedHtml(initialHtml);
    setOriginalText(selected.text);
    setRationale('');
    setSaveError(null);
    setEditorOpen(true);
  }

  function handleCloseEditor() {
    setEditorOpen(false);
    setEditedHtml('');
    setOriginalText('');
    setRationale('');
    setSaveError(null);
  }

  /**
   * Extract plain text from the editor HTML for comparison against original.
   * We use a temporary DOM element to strip HTML tags reliably.
   */
  function editorPlainText(): string {
    const tmp = document.createElement('div');
    tmp.innerHTML = editedHtml;
    return (tmp.textContent || '').trim();
  }

  const isDirty = editorPlainText() !== originalText.trim();

  async function handleSave() {
    if (!selected || !workId || !currentPersona) return;

    setSaving(true);
    setSaveError(null);

    // Strip <p> wrapper from editor HTML — the backend stores plain text.
    // For now we take the innerText; richer formatting handling later.
    const proposedText = editorPlainText();

    const payload: DraftAmendmentCreate = {
      work_id: workId,
      target_eid: selected.eid,
      change_type: 'modify',
      proposed_text: proposedText,
      rationale: rationale.trim() || `Amendment proposed via editor by ${currentPersona.full_name}.`,
      status: 'draft',
      author_user_id: currentPersona.user_id,
      author_unit_id: currentPersona.unit_id,
    };

    try {
      const created = await apiPost<DraftAmendment>('/rbi/drafts/', payload);
      // Success — close modal, briefly show confirmation
      handleCloseEditor();
      setSelected(null);
      setSavedConfirmation(
        `Draft saved: ${created.change_type_display} on ${created.target_eid}`
      );
      // Auto-dismiss confirmation after 5s
      setTimeout(() => setSavedConfirmation(null), 5000);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="document-body">
      <article className="doc-paper">
        <DocumentMasthead xml={xml} />
        <AknRenderer
          xml={xml}
          onSelect={setSelected}
          selectedEid={selected?.eid || null}
        />
      </article>

      {selected && (
        <div className="selection-action-bar">
          <div className="selection-info">
            <span className="selection-label">Selected:</span>
            <span className="selection-eid">{selected.eid}</span>
            <span className="selection-preview">
              "{selected.text.slice(0, 80)}
              {selected.text.length > 80 ? '…' : ''}"
            </span>
          </div>
          <div className="selection-actions">
            <button
              className="btn btn-secondary"
              onClick={() => setSelected(null)}
            >
              Clear selection
            </button>
            <button
              className="btn btn-primary"
              onClick={handleOpenEditor}
            >
              Edit this provision
            </button>
          </div>
        </div>
      )}

      {/* Success toast — floats top-right */}
      {savedConfirmation && (
        <div className="save-toast">
          <span>✓ {savedConfirmation}</span>
          <button
            className="save-toast-close"
            onClick={() => setSavedConfirmation(null)}
            aria-label="Dismiss"
          >
            ×
          </button>
        </div>
      )}

      <Modal
        isOpen={editorOpen}
        onClose={handleCloseEditor}
        title={`Edit provision · ${selected?.eid || ''}`}
        footer={
          <>
            <div className="modal-footer-meta">
              {currentPersona && (
                <span>
                  Drafting as <strong>{currentPersona.full_name}</strong>
                  {' · '}
                  {currentPersona.unit_short_code}
                </span>
              )}
            </div>
            <div className="modal-footer-actions">
              <button
                className="btn btn-secondary"
                onClick={handleCloseEditor}
                disabled={saving}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleSave}
                disabled={!isDirty || saving}
                title={
                  !isDirty
                    ? 'Make an edit to enable save'
                    : saving
                    ? 'Saving...'
                    : 'Save as new draft amendment'
                }
              >
                {saving ? 'Saving...' : 'Save draft'}
              </button>
            </div>
          </>
        }
      >
        <div className="editor-modal-body">
          <div className="editor-modal-instructions">
            <p>
              Editing the text of <code>{selected?.eid}</code>. Save will
              create a new draft amendment authored by the currently-selected
              persona.
            </p>
          </div>

          <TipTapEditor
            initialContent={editedHtml}
            onChange={setEditedHtml}
          />

          <div className="rationale-field">
            <label htmlFor="rationale">
              Rationale <span className="field-optional">(optional)</span>
            </label>
            <textarea
              id="rationale"
              className="rationale-textarea"
              placeholder="Why is this change being proposed?"
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              rows={2}
              disabled={saving}
            />
          </div>

          {saveError && (
            <div className="save-error">
              <strong>Could not save:</strong> {saveError}
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}