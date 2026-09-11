import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { apiFetch } from '../api/client';
import type { Persona, PersonasResponse } from '../api/types';

/**
 * Persona context — provides the currently-active viewing persona
 * to the whole app, and a setter for the dropdown to change it.
 *
 * Persisted in localStorage so a page refresh keeps the last choice.
 */
interface PersonaContextValue {
  personas: Persona[];        // all available personas
  currentPersona: Persona | null;
  setCurrentPersona: (p: Persona) => void;
  loading: boolean;
  error: string | null;
}

const PersonaContext = createContext<PersonaContextValue | undefined>(undefined);

const STORAGE_KEY = 'rbi-registry-current-persona-id';

export function PersonaProvider({ children }: { children: ReactNode }) {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [currentPersona, setCurrentPersonaState] = useState<Persona | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load personas once on app startup, restore saved selection if any
  useEffect(() => {
    async function loadPersonas() {
      try {
        const data = await apiFetch<PersonasResponse>('/rbi/personas/');
        setPersonas(data.personas);

        // Restore last-used persona from localStorage
        const savedIdStr = localStorage.getItem(STORAGE_KEY);
        const savedId = savedIdStr ? parseInt(savedIdStr, 10) : null;
        const restored = savedId
          ? data.personas.find((p) => p.user_id === savedId)
          : null;
        // Default to first persona if nothing saved (or saved user no longer exists)
        setCurrentPersonaState(restored || data.personas[0] || null);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    }
    loadPersonas();
  }, []);

  const setCurrentPersona = (p: Persona) => {
    setCurrentPersonaState(p);
    localStorage.setItem(STORAGE_KEY, String(p.user_id));
  };

  return (
    <PersonaContext.Provider
      value={{ personas, currentPersona, setCurrentPersona, loading, error }}
    >
      {children}
    </PersonaContext.Provider>
  );
}

/**
 * Hook for consuming the persona context in any component.
 * Throws if used outside a PersonaProvider — helpful for catching wiring bugs.
 */
export function usePersona() {
  const ctx = useContext(PersonaContext);
  if (!ctx) {
    throw new Error('usePersona must be used inside a PersonaProvider');
  }
  return ctx;
}