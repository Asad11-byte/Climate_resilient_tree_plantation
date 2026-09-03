import L from "leaflet";

// Vite doesn't resolve Leaflet's default marker image imports correctly out
// of the box; point the default icon at CDN-hosted assets instead of
// wrestling with asset bundling for three small PNGs.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});
