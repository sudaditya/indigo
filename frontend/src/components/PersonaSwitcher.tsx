import { usePersona } from '../context/PersonaContext';

/**
 * "Viewing as" dropdown for persona switching.
 * Renders as a button showing the current persona; clicking it opens
 * a native <select> for the actual switching (simple, accessible,
 * keyboard-friendly out of the box).
 */
export function PersonaSwitcher() {
  const { personas, currentPersona, setCurrentPersona, loading, error } = usePersona();

  if (loading) return <div className="persona-switcher">Loading personas…</div>;
  if (error) return <div className="persona-switcher persona-error">Error: {error}</div>;
  if (!currentPersona) return <div className="persona-switcher">No personas available</div>;

  return (
    <div className="persona-switcher">
      <label className="persona-label">Viewing as</label>
      <select
        className="persona-select"
        value={currentPersona.user_id}
        onChange={(e) => {
          const id = parseInt(e.target.value, 10);
          const chosen = personas.find((p) => p.user_id === id);
          if (chosen) setCurrentPersona(chosen);
        }}
      >
        {personas.map((p) => (
          <option key={p.user_id} value={p.user_id}>
            {p.full_name} · {p.unit_short_code}
          </option>
        ))}
      </select>
    </div>
  );
}