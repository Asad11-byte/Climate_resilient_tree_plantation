import { useCallback, useEffect, useRef, useState } from "react";

/**
 * On/off browser geolocation. When enabled, watches position and keeps
 * `position` updated; when disabled, stops watching and clears it.
 * Deliberately opt-in (starts off) — the map shouldn't request location
 * access without the person explicitly asking for it.
 */
export function useGeolocation() {
  const [enabled, setEnabled] = useState(false);
  const [position, setPosition] = useState(null); // [lat, lon] | null
  const [error, setError] = useState(null);
  const watchIdRef = useRef(null);

  useEffect(() => {
    if (!enabled) {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
      setPosition(null);
      setError(null);
      return;
    }

    if (!navigator.geolocation) {
      setError("Geolocation isn't available in this browser.");
      setEnabled(false);
      return;
    }

    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        setError(null);
        setPosition([pos.coords.latitude, pos.coords.longitude]);
      },
      (err) => {
        setError(err.message || "Couldn't get your location.");
        setEnabled(false);
      },
      { enableHighAccuracy: true, maximumAge: 15000 },
    );

    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
    };
  }, [enabled]);

  const toggle = useCallback(() => setEnabled((v) => !v), []);

  return { enabled, position, error, toggle };
}
