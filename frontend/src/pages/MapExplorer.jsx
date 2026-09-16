import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, Polygon, CircleMarker, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "../components/map/leafletIconFix";
import LocationMarkerLayer from "../components/map/LocationMarkerLayer";
import EnvironmentalPanel from "../components/map/EnvironmentalPanel";
import { useGeolocation } from "../hooks/useGeolocation";
import { MANDI_BAHAUDDIN_RING } from "../components/map/mandiBahauddinRing";
import { isPointInPolygon, boundsFromRing } from "../components/map/geo";

const MANDI_BAHAUDDIN_CENTER = [32.585, 73.5];

// Keep navigation within the district's geographic extent. Selection itself
// is still checked against the precise polygon below, not this rectangle.
const DISTRICT_BOUNDS = boundsFromRing(MANDI_BAHAUDDIN_RING);
const BOUNDARY_PATH_OPTIONS = { color: "#7ed957", weight: 3, fill: false };
const MY_LOCATION_PATH_OPTIONS = { color: "#3d6f8a", fillColor: "#3d6f8a", fillOpacity: 0.9, weight: 2 };

function ToggleButton({ active, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-md border px-3 py-1.5 text-xs font-medium transition ${
        active
          ? "border-leaf-600 bg-leaf-600 text-white"
          : "border-bark-500/25 bg-card text-soil-900 hover:border-soil-800/40"
      }`}
    >
      {children}
    </button>
  );
}

function LocationIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={className} aria-hidden="true">
      <path d="M12 21s7-5.4 7-12a7 7 0 1 0-14 0c0 6.6 7 12 7 12Z" />
      <circle cx="12" cy="9" r="2.25" />
    </svg>
  );
}

function FitDistrictControl({ request }) {
  const map = useMap();

  useEffect(() => {
    map.fitBounds(DISTRICT_BOUNDS, { padding: [28, 28], maxZoom: 11, animate: request > 0 });
  }, [map, request]);

  return null;
}

function MapSizeSync() {
  const map = useMap();

  useEffect(() => {
    // Synchronize only when the map container's dimensions actually change.
    // This fixes the initial measurement race without redrawing whenever the
    // pointer moves over the map or the user pans it.
    let frame;
    const syncSize = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => map.invalidateSize({ animate: false, pan: false, debounceMoveend: true }));
    };
    const observer = new ResizeObserver(syncSize);
    observer.observe(map.getContainer());
    syncSize();

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [map]);

  return null;
}

function ExpandIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={className} aria-hidden="true">
      <path d="M8 3H3v5M16 3h5v5M21 16v5h-5M3 16v5h5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M3 8l6-5M21 8l-6-5M21 16l-6 5M3 16l6 5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function CursorClickIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className={className} aria-hidden="true">
      <path d="M9 4.5 19 12l-4.6 1.3L12 19 9 4.5Z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/**
 * Shown in place of the environmental readings when nothing has been picked
 * yet. Previously the "no selection" case was communicated only by a small
 * grey line of helper text plus EnvironmentalPanel's own empty state, and
 * the primary action button was hidden entirely — so a first-time user had
 * no clear signal about what the page wanted from them, or why they
 * couldn't proceed. This makes the prerequisite explicit and actionable.
 */
function NoSelectionPrompt({ onShowDistrict, onUseMyLocation, geolocationEnabled }) {
  return (
    <div className="rounded-lg border border-dashed border-leaf-600/40 bg-leaf-100/40 px-4 py-5 text-center">
      <span className="mx-auto flex h-9 w-9 items-center justify-center rounded-full bg-leaf-600/15">
        <CursorClickIcon className="h-4.5 w-4.5 text-leaf-700" />
      </span>
      <p className="mt-3 text-sm font-semibold text-soil-900">No location selected yet</p>
      <p className="mx-auto mt-1.5 max-w-[15rem] text-xs leading-relaxed text-bark-700">
        Click any point inside the green district boundary to load its soil, climate, and vegetation data.
      </p>
      <div className="mt-3.5 flex flex-col gap-1.5">
        {!geolocationEnabled && (
          <button
            type="button"
            onClick={onUseMyLocation}
            className="text-xs font-medium text-leaf-700 underline decoration-leaf-600/40 underline-offset-2 transition hover:decoration-leaf-600"
          >
            Or use my current location
          </button>
        )}
        <button
          type="button"
          onClick={onShowDistrict}
          className="text-xs font-medium text-bark-700 underline decoration-bark-500/30 underline-offset-2 transition hover:text-soil-900"
        >
          Show the full district
        </button>
      </div>
    </div>
  );
}

// `mapSelection` ({ latitude, longitude } | null) and `environment`
// ({ data, loading, error, fetchAt }) are now owned by ProtectedApp (see
// App.jsx) and passed in as props, same reason chat/conversations were
// lifted out of AIAssistant — this component no longer owns `position` or
// `useEnvironment()` locally, so navigating away and back no longer loses
// the clicked point or its fetched data.
export default function MapExplorer({ onSelect, mapSelection, environment }) {
  const navigate = useNavigate();
  const { data, loading, error, fetchAt } = environment;
  const [outsideNotice, setOutsideNotice] = useState(false);
  const [fitRequest, setFitRequest] = useState(0);
  const geolocation = useGeolocation();

  // Derived, not stored — mapSelection is the single source of truth
  // ({ latitude, longitude }); react-leaflet/geo helpers below all expect
  // [lat, lon], so that conversion happens here, once, rather than keeping
  // a second array-shaped copy of the same value in its own state.
  const position = mapSelection ? [mapSelection.latitude, mapSelection.longitude] : null;
  const hasSelection = Boolean(position);

  const isMyLocationInDistrict = useMemo(
    () => (geolocation.position ? isPointInPolygon(...geolocation.position, MANDI_BAHAUDDIN_RING) : null),
    [geolocation.position],
  );

  const handlePick = (lat, lon) => {
    if (!isPointInPolygon(lat, lon, MANDI_BAHAUDDIN_RING)) {
      setOutsideNotice(true);
      return;
    }
    setOutsideNotice(false);
    onSelect(lat, lon);
    fetchAt(lat, lon);
  };

  const handleAskAboutLocation = () => {
    navigate("/assistant");
  };

  const selectionLabel = position ? `${position[0].toFixed(4)}, ${position[1].toFixed(4)}` : null;

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-[var(--font-display)] text-2xl font-semibold text-soil-900">Map Explorer</h1>
          <p className="mt-1 max-w-2xl text-sm text-bark-700">
            Select a point inside the green district boundary to inspect local conditions, then take that location to
            the assistant for an evidence-backed recommendation.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-md border border-leaf-600/30 bg-leaf-100 px-3 py-1.5 text-xs font-medium text-leaf-700">
            <span className="h-1.5 w-1.5 rounded-full bg-leaf-600" aria-hidden="true" />
            District coverage
          </span>
          <ToggleButton active={geolocation.enabled} onClick={geolocation.toggle}>
            Use my location
          </ToggleButton>
          <button
            type="button"
            onClick={() => setFitRequest((value) => value + 1)}
            className="inline-flex items-center gap-1.5 rounded-md border border-bark-500/25 bg-card px-3 py-1.5 text-xs font-medium text-soil-900 transition hover:border-leaf-600/50"
          >
            <ExpandIcon className="h-3.5 w-3.5" />
            Show full district
          </button>
        </div>
      </div>

      {geolocation.error && <p className="mt-3 rounded-lg border border-danger/25 bg-danger-subtle px-3 py-2 text-xs text-danger">{geolocation.error}</p>}
      {geolocation.enabled && isMyLocationInDistrict === false && (
        <p className="mt-3 rounded-lg border border-warning/25 bg-warning-subtle px-3 py-2 text-xs text-warning">
          Your current location is outside the district. You can still view it on the map, but recommendations only
          support points within Mandi Bahauddin.
        </p>
      )}

      <div className="mt-4 grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        <div className="relative h-[420px] overflow-hidden rounded-xl border border-bark-500/15 shadow-sm sm:h-[520px]">
          {/* The on-map hint stays visible until a point is actually chosen,
              then gets out of the way — once the user has selected, the
              instruction is noise and the panel carries the state instead. */}
          {!hasSelection && (
            <div className="pointer-events-none absolute left-3 top-3 z-[500] rounded-lg border border-leaf-600/30 bg-card/95 px-3 py-2 shadow-sm">
              <p className="flex items-center gap-1.5 text-xs font-semibold text-soil-900">
                <LocationIcon className="h-3.5 w-3.5 text-leaf-700" /> Click within the green boundary
              </p>
              <p className="mt-0.5 text-[0.7rem] text-bark-700">Outside areas are not covered.</p>
            </div>
          )}
          <MapContainer
            center={MANDI_BAHAUDDIN_CENTER}
            zoom={11}
            minZoom={9}
            maxZoom={16}
            maxBounds={DISTRICT_BOUNDS}
            maxBoundsViscosity={1.0}
            attributionControl={false}
            className="h-full w-full"
          >
            <MapSizeSync />
            <FitDistrictControl request={fitRequest} />
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

            <Polygon positions={MANDI_BAHAUDDIN_RING} pathOptions={BOUNDARY_PATH_OPTIONS} interactive={false} />

            {geolocation.position && (
              <CircleMarker center={geolocation.position} radius={7} pathOptions={MY_LOCATION_PATH_OPTIONS} />
            )}

            <LocationMarkerLayer position={position} onPick={handlePick} />
          </MapContainer>
          <a
            href="https://www.openstreetmap.org/copyright"
            target="_blank"
            rel="noreferrer"
            className="absolute bottom-1 right-1 z-[500] rounded bg-card/90 px-1.5 py-0.5 text-[0.65rem] text-bark-700 shadow-sm hover:text-leaf-700"
          >
            © OpenStreetMap contributors
          </a>
        </div>

        <div className="rounded-xl border border-bark-500/15 bg-card p-4 shadow-sm">
          <div className="mb-4 border-b border-bark-500/15 pb-3">
            <h2 className="font-[var(--font-display)] text-lg font-semibold text-soil-900">Environmental data</h2>
            {selectionLabel ? (
              <p className="mt-1 text-xs text-bark-700">Selected point: <span className="font-medium text-soil-900">{selectionLabel}</span></p>
            ) : (
              <p className="mt-1 text-xs text-bark-700">Nothing selected yet.</p>
            )}
          </div>

          {outsideNotice && !hasSelection && (
            <p className="mb-3 rounded-lg border border-warning/25 bg-warning-subtle px-3 py-2 text-xs text-warning">
              That point is outside the district boundary. Select a point within the green outline to continue.
            </p>
          )}

          {hasSelection ? (
            <EnvironmentalPanel
              position={position}
              loading={loading}
              error={error}
              data={data}
              onRetry={() => position && fetchAt(position[0], position[1])}
            />
          ) : (
            <NoSelectionPrompt
              geolocationEnabled={geolocation.enabled}
              onUseMyLocation={geolocation.toggle}
              onShowDistrict={() => setFitRequest((value) => value + 1)}
            />
          )}

          {/* Rendered in both states rather than hidden until a point exists:
              a disabled control with a reason tells a first-time user what
              the page is for and what's blocking them, where an absent
              control tells them nothing. */}
          <button
            onClick={handleAskAboutLocation}
            disabled={!hasSelection}
            title={hasSelection ? undefined : "Select a location on the map first"}
            className="mt-4 w-full rounded-lg bg-leaf-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-leaf-600 disabled:cursor-not-allowed disabled:bg-bark-500/25 disabled:text-bark-700 disabled:hover:bg-bark-500/25"
          >
            {hasSelection ? "Ask about this location →" : "Select a location first"}
          </button>
        </div>
      </div>
    </div>
  );
}