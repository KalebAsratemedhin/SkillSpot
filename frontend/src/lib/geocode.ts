/** Place search via Photon (OSM) — same primary source Yetbota uses server-side. */

export type GeoHit = {
  lat: number
  lng: number
  label: string
  kind?: string
}

const PHOTON = 'https://photon.komoot.io'
/** Soft bias toward Addis Ababa metro. */
const DEFAULT_BIAS = { lat: 9.03, lng: 38.74 }

function asFinite(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim() !== '') {
    const n = Number(value)
    return Number.isFinite(n) ? n : null
  }
  return null
}

function photonLabel(props: Record<string, unknown>): string {
  const parts = [
    props.name,
    props.housenumber && props.street
      ? `${props.housenumber} ${props.street}`
      : props.street,
    props.city ?? props.district ?? props.county,
    props.state,
    props.country,
  ].filter((p): p is string => typeof p === 'string' && p.trim().length > 0)
  const unique: string[] = []
  for (const p of parts) {
    if (!unique.includes(p)) unique.push(p)
  }
  return unique.join(', ') || 'Unknown place'
}

export async function searchPlaces(
  q: string,
  bias?: { lat: number; lng: number },
  signal?: AbortSignal
): Promise<GeoHit[]> {
  const query = q.trim()
  if (query.length < 2) return []

  const lat = bias && Number.isFinite(bias.lat) ? bias.lat : DEFAULT_BIAS.lat
  const lng = bias && Number.isFinite(bias.lng) ? bias.lng : DEFAULT_BIAS.lng
  const url =
    `${PHOTON}/api/?q=${encodeURIComponent(query)}` +
    `&lat=${lat}&lon=${lng}&limit=8&lang=en`

  const res = await fetch(url, {
    headers: { Accept: 'application/json' },
    signal,
  })
  if (!res.ok) throw new Error('Place lookup failed')

  const data: unknown = await res.json()
  if (!data || typeof data !== 'object') return []
  const features = (data as { features?: unknown }).features
  if (!Array.isArray(features)) return []

  const hits: GeoHit[] = []
  for (const f of features) {
    if (!f || typeof f !== 'object') continue
    const feature = f as {
      geometry?: { coordinates?: unknown }
      properties?: Record<string, unknown>
    }
    const coords = feature.geometry?.coordinates
    if (!Array.isArray(coords) || coords.length < 2) continue
    const hitLng = asFinite(coords[0])
    const hitLat = asFinite(coords[1])
    if (hitLat == null || hitLng == null) continue
    const props = feature.properties ?? {}
    const kind =
      typeof props.osm_value === 'string'
        ? props.osm_value
        : typeof props.osm_key === 'string'
          ? props.osm_key
          : undefined
    hits.push({
      lat: hitLat,
      lng: hitLng,
      label: photonLabel(props),
      kind,
    })
  }
  return hits
}

export async function reversePlace(
  lat: number,
  lng: number,
  signal?: AbortSignal
): Promise<string> {
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    throw new Error('Invalid coordinates')
  }
  const url = `${PHOTON}/reverse?lat=${encodeURIComponent(String(lat))}&lon=${encodeURIComponent(String(lng))}&lang=en`
  const res = await fetch(url, {
    headers: { Accept: 'application/json' },
    signal,
  })
  if (!res.ok) throw new Error('Reverse lookup failed')
  const data: unknown = await res.json()
  if (!data || typeof data !== 'object') {
    return `${lat.toFixed(5)}, ${lng.toFixed(5)}`
  }
  const features = (data as { features?: unknown }).features
  if (!Array.isArray(features) || !features[0] || typeof features[0] !== 'object') {
    return `${lat.toFixed(5)}, ${lng.toFixed(5)}`
  }
  const props =
    (features[0] as { properties?: Record<string, unknown> }).properties ?? {}
  return photonLabel(props)
}
