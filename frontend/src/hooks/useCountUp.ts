import { useEffect, useRef, useState } from 'react';

const prefersReducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/**
 * Eases a displayed number from its previous value to `target` so a change
 * reads as movement rather than a swap. Jumps straight to the target when
 * `animate` is false (e.g. while data is loading) or the user prefers
 * reduced motion.
 */
export function useCountUp(target: number, { animate = true, duration = 400 } = {}): number {
  const [value, setValue] = useState(target);
  const shownRef = useRef(target);
  const couldAnimate = useRef(animate);

  useEffect(() => {
    const from = shownRef.current;
    // The render that first enables animation (e.g. data just arrived) snaps
    // to its value; only later changes count.
    const justEnabled = !couldAnimate.current;
    couldAnimate.current = animate;
    // A hidden page gets no animation frames, so it would never land.
    if (!animate || justEnabled || from === target || document.hidden || prefersReducedMotion()) {
      shownRef.current = target;
      setValue(target);
      return;
    }

    let frame = 0;
    // Time from the first frame's own timestamp: rAF timestamps can predate
    // performance.now() taken here, which would make t negative.
    let start: number | null = null;
    const tick = (now: number) => {
      start ??= now;
      const t = Math.min(Math.max((now - start) / duration, 0), 1);
      const eased = 1 - Math.pow(1 - t, 4); // decelerate, matching --ease-settle
      shownRef.current = from + (target - from) * eased;
      setValue(t === 1 ? target : shownRef.current);
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, animate, duration]);

  return value;
}
