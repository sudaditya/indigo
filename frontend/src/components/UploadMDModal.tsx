import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Modal } from './Modal';
import { apiPostForm } from '../api/client';
import type { UploadedMDResponse } from '../api/types';

interface UploadMDModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Called after a successful upload with the new MD's ID. */
  onSuccess?: (uploaded: UploadedMDResponse) => void;
}

/**
 * Modal for uploading a new Master Direction PDF.
 *
 * Flow:
 *   1. User picks a PDF file + fills in number, date, title
 *   2. Click Upload → shows spinner (Gemini call is 15-60 sec)
 *   3. On success: close, navigate to /works/:id/content
 *   4. On error: show error message inline, keep form data
 */
export function UploadMDModal({ isOpen, onClose, onSuccess }: UploadMDModalProps) {
  const navigate = useNavigate();

  const [file, setFile] = useState<File | null>(null);
  const [number, setNumber] = useState('');
  const [date, setDate] = useState('');
  const [title, setTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function resetForm() {
    setFile(null);
    setNumber('');
    setDate('');
    setTitle('');
    setError(null);
  }

  function handleClose() {
    if (uploading) return; // don't allow close mid-upload
    resetForm();
    onClose();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !number || !date || !title) {
      setError('All fields are required.');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('pdf_file', file);
    formData.append('number', number);
    formData.append('date', date);
    formData.append('title', title);

    try {
      const uploaded = await apiPostForm<UploadedMDResponse>(
        '/rbi/upload-md/',
        formData
      );

      // Success — close, notify parent, navigate to the new MD
      resetForm();
      onClose();
      if (onSuccess) onSuccess(uploaded);
      // Small delay so success toast is visible before navigation
      setTimeout(() => navigate(`/works/${uploaded.id}/content`), 300);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploading(false);
    }
  }

  const canSubmit = file && number && date && title && !uploading;

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Upload Master Direction"
      footer={
        <>
          <div className="modal-footer-meta">
            {uploading && (
              <span className="upload-status">
                <span className="spinner"></span>
                Processing… this may take 30-60 seconds
              </span>
            )}
          </div>
          <div className="modal-footer-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleClose}
              disabled={uploading}
            >
              Cancel
            </button>
            <button
              type="submit"
              form="upload-md-form"
              className="btn btn-primary"
              disabled={!canSubmit}
            >
              {uploading ? 'Uploading…' : 'Upload'}
            </button>
          </div>
        </>
      }
    >
      <form id="upload-md-form" onSubmit={handleSubmit} className="upload-form">
        <div className="upload-instructions">
          <p>
            Upload an RBI Master Direction PDF. The document will be extracted,
            structured into Akoma Ntoso format, and made available for
            editing.
          </p>
        </div>

        {/* File picker */}
        <div className="form-field">
          <label htmlFor="pdf_file">
            PDF file <span className="required">*</span>
          </label>
          <input
            id="pdf_file"
            type="file"
            accept=".pdf,application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            disabled={uploading}
            required
          />
          {file && (
            <div className="file-info">
              Selected: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(0)} KB)
            </div>
          )}
        </div>

        {/* MD number */}
        <div className="form-field">
          <label htmlFor="number">
            MD number <span className="required">*</span>
          </label>
          <input
            id="number"
            type="text"
            placeholder="e.g. 290"
            value={number}
            onChange={(e) => setNumber(e.target.value)}
            disabled={uploading}
            required
          />
          <div className="field-hint">
            The MD number, without prefix. E.g. "290" not "MD 290".
          </div>
        </div>

        {/* Date */}
        <div className="form-field">
          <label htmlFor="date">
            Publication date <span className="required">*</span>
          </label>
          <input
            id="date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            disabled={uploading}
            required
          />
          <div className="field-hint">
            Date on the MD's cover page.
          </div>
        </div>

        {/* Title */}
        <div className="form-field">
          <label htmlFor="title">
            Title <span className="required">*</span>
          </label>
          <input
            id="title"
            type="text"
            placeholder="e.g. Reserve Bank of India (Urban Co-operative Banks…) Directions, 2025"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={uploading}
            required
          />
          <div className="field-hint">
            Full RBI title as it appears on the document.
          </div>
        </div>

        {error && (
          <div className="upload-error">
            <strong>Upload failed:</strong> {error}
          </div>
        )}
      </form>
    </Modal>
  );
}