import L from 'leaflet'

/** CSS pin — avoids Vite breaking Leaflet's default marker image URLs. */
export function createMapPinIcon(Lns: typeof L = L): L.DivIcon {
  return Lns.divIcon({
    className: 'ss-map-pin',
    html: '<span class="ss-map-pin-inner"></span>',
    iconSize: [32, 40],
    iconAnchor: [16, 38],
    popupAnchor: [0, -36],
    tooltipAnchor: [0, -36],
  })
}

export const DEFAULT_MAP_CENTER = { lat: 9.03, lng: 38.74 } as const

/**
 * OSM.de tiles — lighter/faster than CyclOSM, no API key.
 * Avoid tile.openstreetmap.org (OSMF often serves blank blocked PNGs to apps).
 * No tileerror basemap swap: aborted loads during zoom fire tileerror and would
 * tear off the layer → gray map with pin still visible.
 */
export const OSM_DE_TILE_URL = 'https://tile.openstreetmap.de/{z}/{x}/{y}.png'
export const OSM_DE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'

/** @deprecated Prefer OSM_DE_* / addBasemapTiles */
export const OSM_TILE_URL = OSM_DE_TILE_URL
/** @deprecated Prefer OSM_DE_* */
export const OSM_ATTRIBUTION = OSM_DE_ATTRIBUTION
/** @deprecated Prefer OSM_DE_* */
export const MAP_TILE_URL = OSM_DE_TILE_URL
/** @deprecated Prefer OSM_DE_* */
export const MAP_ATTRIBUTION = OSM_DE_ATTRIBUTION

export function addBasemapTiles(map: L.Map, Lns: typeof L = L): L.TileLayer {
  const layer = Lns.tileLayer(OSM_DE_TILE_URL, {
    attribution: OSM_DE_ATTRIBUTION,
    maxZoom: 19,
  })
  layer.addTo(map)
  return layer
}
