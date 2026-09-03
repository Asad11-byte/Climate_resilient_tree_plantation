import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "../components/map/leafletIconFix";
import LocationMarkerLayer from "../components/map/LocationMarkerLayer";
import EnvironmentalPanel from "../components/map/EnvironmentalPanel";
import { useEnvironment } from "../hooks/useEnvironment";

const MANDI_BAHAUDDIN_CENTER = [32.585, 73.492];

export default function MapExplorer({ onSelect }) {
  const navigate = useNavigate();
  const { data, loading, error, fetchAt } = useEnvironment();
  const [position, setPosition] = useState(null); // [lat, lon] of the clicked point

  const handlePick = (lat, lon) => {
    setPosition([lat, lon]);
    onSelect(lat, lon);
    fetchAt(lat, lon);
  };

  const handleAskAboutLocation = () => {
    navigate("/assistant");
  };

  return (
    <div>
      <h1 className="font-[var(--font-display)] text-2xl font-semibold text-soil-900">Map Explorer</h1>
      <p className="mt-1 text-sm text-bark-700">
        Click anywhere in Mandi Bahauddin to see the environmental data behind a recommendation.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        <div className="h-[520px] overflow-hidden rounded-lg border border-bark-500/15">
          <MapContainer center={MANDI_BAHAUDDIN_CENTER} zoom={11} className="h-full w-full">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <LocationMarkerLayer position={position} onPick={handlePick} />
          </MapContainer>
        </div>

        <div className="rounded-lg border border-bark-500/15 bg-parchment-100/40 p-4">
          <h2 className="mb-3 font-[var(--font-display)] text-lg font-semibold text-soil-900">
            Environmental Data
          </h2>
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
