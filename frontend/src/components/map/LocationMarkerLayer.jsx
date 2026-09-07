import { Marker, useMapEvents } from "react-leaflet";

/**
 * Invisible layer that listens for map clicks and reports the coordinate up
 * to the parent. Renders the marker for the current selection, unless
 * `showMarker` is false — the click listener still fires either way, so
 * hiding the pin never breaks the underlying data lookup.
 */
export default function LocationMarkerLayer({ position, onPick, showMarker = true }) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng);
    },
  });

  if (!position || !showMarker) return null;
  return <Marker position={position} />;
}