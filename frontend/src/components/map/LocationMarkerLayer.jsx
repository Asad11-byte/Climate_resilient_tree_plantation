import { Marker, useMapEvents } from "react-leaflet";

/**
 * Invisible layer that listens for map clicks and reports the coordinate up
 * to the parent. Renders the marker for the current selection, if any.
 */
export default function LocationMarkerLayer({ position, onPick }) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng);
    },
  });

  if (!position) return null;
  return <Marker position={position} />;
}
