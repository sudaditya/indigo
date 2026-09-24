
/**
 * Reusable tooltip that appears on hover after a short delay,
 * disappears quickly, and stays visible while the mouse is over the trigger.
 *
 * Positioning: centered above the trigger by default, with an arrow.
 * Fallback: below the trigger if there isn't room above.
 *
 * Usage:
 *   <Tooltip content="Explanation here">
 *     <button>Hover me</button>
 *   </Tooltip>
 *
 * The child is the trigger element. Tooltip wraps it in a span so the
 * child keeps its native behavior (button clicks, cursor styles, etc.).
 */
import { useState, useRef, useEffect } from 'react';
import type { ReactNode } from 'react';

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  /** Delay (ms) before showing on hover. Default 300. */
  delay?: number;
  /** Preferred position — 'top' (default) or 'bottom'. Auto-flips if no room. */
  placement?: 'top' | 'bottom';
}

export function Tooltip({
  content,
  children,
  delay = 300,
  placement = 'top',
}: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const [actualPlacement, setActualPlacement] = useState<'top' | 'bottom'>(placement);
  const timerRef = useRef<number | null>(null);
  const triggerRef = useRef<HTMLSpanElement>(null);

  function handleEnter() {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => {
      // Decide top or bottom based on viewport space
      const rect = triggerRef.current?.getBoundingClientRect();
      if (rect) {
        const spaceAbove = rect.top;
        const spaceBelow = window.innerHeight - rect.bottom;
        if (placement === 'top' && spaceAbove < 60 && spaceBelow > 60) {
          setActualPlacement('bottom');
        } else if (placement === 'bottom' && spaceBelow < 60 && spaceAbove > 60) {
          setActualPlacement('top');
        } else {
          setActualPlacement(placement);
        }
      }
      setVisible(true);
    }, delay);
  }

  function handleLeave() {
    if (timerRef.current) clearTimeout(timerRef.current);
    setVisible(false);
  }

  // Cleanup pending timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return (
    <span
      ref={triggerRef}
      className="tooltip-trigger"
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
      onFocus={handleEnter}
      onBlur={handleLeave}
    >
      {children}
      {visible && (
        <span className={`tooltip tooltip-${actualPlacement}`} role="tooltip">
          {content}
        </span>
      )}
    </span>
  );
}