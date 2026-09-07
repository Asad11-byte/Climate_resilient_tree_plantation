/**
 * Small geometry helpers for working with the district boundary ring.
 * Everything here takes/returns [lat, lon] pairs (Leaflet's convention),
 * not GeoJSON's [lon, lat] — conversion happens once, where the boundary
 * file is loaded (see mandiBahauddinRing.js).
 */

/** Standard ray-casting point-in-polygon test. */
export function isPointInPolygon(lat, lon, ringLatLng) {
  let inside = false;
  for (let i = 0, j = ringLatLng.length - 1; i < ringLatLng.length; j = i++) {
    const [latI, lonI] = ringLatLng[i];
    const [latJ, lonJ] = ringLatLng[j];
    const intersects =
      latI > lat !== latJ > lat &&
      lon < ((lonJ - lonI) * (lat - latI)) / (latJ - latI) + lonI;
    if (intersects) inside = !inside;
  }
  return inside;
}

/** [[southLat, westLon], [northLat, eastLon]] — what Leaflet's maxBounds/fitBounds expect. */
export function boundsFromRing(ringLatLng, paddingDegrees = 0) {
  const lats = ringLatLng.map((p) => p[0]);
  const lons = ringLatLng.map((p) => p[1]);
  return [
    [Math.min(...lats) - paddingDegrees, Math.min(...lons) - paddingDegrees],
    [Math.max(...lats) + paddingDegrees, Math.max(...lons) + paddingDegrees],
  ];
}

/** Turns a [[south, west], [north, east]] bounds pair into a 4-point
 * rectangle ring, in the order Leaflet's Polygon expects. Used to build a
 * mask ring that's comfortably larger than the pannable area without
 * being world-sized — a huge mask polygon is what causes visible
 * flicker/glitching on pan and zoom, since the renderer has to redraw an
 * enormous shape every frame for no visual benefit (maxBounds already
 * stops the view from ever reaching past it). */
export function rectRingFromBounds(bounds, extraPaddingDegrees = 0) {
  const [[south, west], [north, east]] = bounds;
  const s = south - extraPaddingDegrees;
  const w = west - extraPaddingDegrees;
  const n = north + extraPaddingDegrees;
  const e = east + extraPaddingDegrees;
  return [
    [s, w],
    [n, w],
    [n, e],
    [s, e],
  ];
}