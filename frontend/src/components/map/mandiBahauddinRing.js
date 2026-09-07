import boundaryGeoJSON from "../../data/mandiBahauddinBoundary.json";

// Source: geoBoundaries (CC BY 4.0), ADM2 (district) level for Pakistan —
// https://www.geoboundaries.org, sourced from the Pakistan Census Office /
// OCHA. This is the real administrative boundary, not an approximated
// bounding box. GeoJSON stores coordinates as [lon, lat]; Leaflet wants
// [lat, lon], so the conversion happens once here rather than at every
// call site.
const rawRing = boundaryGeoJSON.features[0].geometry.coordinates[0];

export const MANDI_BAHAUDDIN_RING = rawRing.map(([lon, lat]) => [lat, lon]);
