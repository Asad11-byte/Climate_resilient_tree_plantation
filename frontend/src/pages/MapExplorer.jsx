import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, Polygon, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "../components/map/leafletIconFix";
import LocationMarkerLayer from "../components/map/LocationMarkerLayer";
import EnvironmentalPanel from "../components/map/EnvironmentalPanel";
import { useEnvironment } from "../hooks/useEnvironment";
import { useGeolocation } from "../hooks/useGeolocation";
import { MANDI_BAHAUDDIN_RING } from "../components/map/mandiBahauddinRing";
import { isPointInPolygon, boundsFromRing, rectRingFromBounds } from "../components/map/geo";

const MANDI_BAHAUDDIN_CENTER = [32.585, 73.5];

const DISTRICT_BOUNDS = boundsFromRing(MANDI_BAHAUDDIN_RING, 0.06);

// The mask only needs to cover a bit more than the pannable area —
// maxBounds already makes it impossible to scroll past DISTRICT_BOUNDS,
// so a mask sized to the whole world was pure waste: Leaflet's SVG
// renderer has to redraw that huge shape on every pan/zoom frame, which is
// what caused the visible flicker/glitching. A rectangle a few degrees
// past the pannable area covers every frame that can ever actually be
// seen, at a fraction of the coordinate range.
const MASK_RING = rectRingFromBounds(DISTRICT_BOUNDS, 2);

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

export default function MapExplorer({ onSelect }) {
  const navigate = useNavigate();
  const { data, loading, error, fetchAt } = useEnvironment();
  const [position, setPosition] = useState(null);
  const [outsideNotice, setOutsideNotice] = useState(false);
  const [showBoundary, setShowBoundary] = useState(true);
  const [showMarker, setShowMarker] = useState(true);
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

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-[var(--font-display)] text-2xl font-semibold text-soil-900">Map Explorer</h1>
          <p className="mt-1 text-sm text-bark-700">
            Click anywhere inside Mandi Bahauddin district to see the environmental data behind a
            recommendation — the map is scoped to the district's real administrative boundary.
          </p>
        </div>
        <div className="flex gap-2">
          <ToggleButton active={showBoundary} onClick={() => setShowBoundary((v) => !v)}>
            Boundary
          </ToggleButton>
          <ToggleButton active={showMarker} onClick={() => setShowMarker((v) => !v)}>
            Marker
          </ToggleButton>
          <ToggleButton active={geolocation.enabled} onClick={geolocation.toggle}>
            My Location
          </ToggleButton>
        </div>
      </div>

      {geolocation.error && <p className="mt-2 text-xs text-clay-600">{geolocation.error}</p>}
      {geolocation.enabled && isMyLocationInDistrict === false && (
        <p className="mt-2 text-xs text-amber-500">
          Your current location is outside Mandi Bahauddin district — shown on the map, but out of the
          system's coverage area.
        </p>
      )}

      <div className="mt-4 grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        <div className="h-[520px] overflow-hidden rounded-lg border border-bark-500/15">
          <MapContainer
            center={MANDI_BAHAUDDIN_CENTER}
            zoom={11}
            minZoom={10}
            maxZoom={16}
            maxBounds={DISTRICT_BOUNDS}
            maxBoundsViscosity={1.0}
            preferCanvas
            className="h-full w-full"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {showBoundary && (
              <>
                <Polygon
                  positions={[MASK_RING, MANDI_BAHAUDDIN_RING]}
                  pathOptions={{ color: "transparent", fillColor: "#17130f", fillOpacity: 0.55, stroke: false }}
                  interactive={false}
                />
                <Polygon
                  positions={MANDI_BAHAUDDIN_RING}
                  pathOptions={{ color: "#7ed957", weight: 2, fill: false }}
                  interactive={false}
                />
              </>
            )}

            {geolocation.position && (
              <CircleMarker
                center={geolocation.position}
                radius={7}
                pathOptions={{ color: "#3d6f8a", fillColor: "#3d6f8a", fillOpacity: 0.9, weight: 2 }}
              />
            )}

            <LocationMarkerLayer position={position} onPick={handlePick} showMarker={showMarker} />
          </MapContainer>
        </div>

        <div className="rounded-lg border border-bark-500/15 bg-panel/40 p-4">
          <h2 className="mb-3 font-[var(--font-display)] text-lg font-semibold text-soil-900">
            Environmental Data
          </h2>
          {outsideNotice && !position && (
            <p className="mb-3 text-xs text-amber-500">
              That point is outside Mandi Bahauddin district — click inside the boundary to look up data.
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
              className="mt-4 w-full rounded-md bg-leaf-700 px-4 py-2 text-sm font-medium text-parchment-50 transition hover:bg-leaf-600"
            >
              Ask about this location
            </button>
          )}
        </div>
      </div>
    </div>
  );
}