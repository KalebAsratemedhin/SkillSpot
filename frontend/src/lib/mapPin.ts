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
export const OSM_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
export const OSM_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
