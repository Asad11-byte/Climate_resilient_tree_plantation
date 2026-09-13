import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, Polygon, CircleMarker, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "../components/map/leafletIconFix";
import LocationMarkerLayer from "../components/map/LocationMarkerLayer";
import EnvironmentalPanel from "../components/map/EnvironmentalPanel";
import { useEnvironment } from "../hooks/useEnvironment";
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

export default function MapExplorer({ onSelect }) {
  const navigate = useNavigate();
  const { data, loading, error, fetchAt } = useEnvironment();
  const [position, setPosition] = useState(null);
  const [outsideNotice, setOutsideNotice] = useState(false);
  const [fitRequest, setFitRequest] = useState(0);
  const geolocation = useGeolocation();

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
    setPosition([lat, lon]);
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
          <div className="pointer-events-none absolute left-3 top-3 z-[500] rounded-lg border border-bark-500/15 bg-card/95 px-3 py-2 shadow-sm">
            <p className="flex items-center gap-1.5 text-xs font-semibold text-soil-900"><LocationIcon className="h-3.5 w-3.5 text-leaf-700" /> Click within the green boundary</p>
            <p className="mt-0.5 text-[0.7rem] text-bark-700">Outside areas are not covered.</p>
          </div>
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
              <p className="mt-1 text-xs text-bark-700">Choose a point on the map to begin.</p>
            )}
          </div>
          {outsideNotice && !position && (
            <p className="mb-3 rounded-lg border border-warning/25 bg-warning-subtle px-3 py-2 text-xs text-warning">
              That point is outside the district boundary. Select a point within the green outline to continue.
            </p>
          )}
          <EnvironmentalPanel
            position={position}
            loading={loading}
            error={error}
            data={data}
            onRetry={() => position && fetchAt(position[0], position[1])}
          />
          {position && (
            <button
              onClick={handleAskAboutLocation}
              className="mt-4 w-full rounded-lg bg-leaf-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-leaf-600"
            >
              Ask about this location →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
