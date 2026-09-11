import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';

/**
 * Minimal TipTap editor for early validation.
 * No AKN integration yet, no save, no track changes.
 * Just: does TipTap render, accept typing, and let us extract content?
 *
 * Props:
 *   initialContent — HTML string to populate the editor with initially
 *   onChange       — called on every edit with the current HTML
 */
interface TipTapEditorProps {
  initialContent?: string;
  onChange?: (html: string) => void;
}

export function TipTapEditor({ initialContent = '', onChange }: TipTapEditorProps) {
  // useEditor sets up ProseMirror internally, keeps the editor instance
  // alive across React re-renders, and cleans up on unmount.
  const editor = useEditor({
    extensions: [StarterKit],
    content: initialContent,
    onUpdate: ({ editor }) => {
      // Fires on every content change (keystroke, formatting toggle, etc.)
      if (onChange) {
        onChange(editor.getHTML());
      }
    },
  });

  if (!editor) return <p>Loading editor…</p>;

  return (
    <div className="tiptap-wrapper">
      <EditorContent editor={editor} />
    </div>
  );
}