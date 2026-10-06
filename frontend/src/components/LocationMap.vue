<template>
  <div class="ss-location-map relative isolate h-full min-h-0 w-full overflow-hidden bg-slate-100">
    <div ref="containerEl" class="absolute inset-0 h-full w-full" />
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type { Map as LeafletMap, Marker as LeafletMarker } from 'leaflet'
import {
  createMapPinIcon,
  DEFAULT_MAP_CENTER,
  OSM_ATTRIBUTION,
  OSM_TILE_URL,
} from '@/lib/mapPin'

const props = withDefaults(
  defineProps<{
    lat?: number | null
    lng?: number | null
    /** Show the pin when coords are valid. Default: true when lat/lng are finite. */
    pinned?: boolean
    interactive?: boolean
    tooltip?: string
    zoom?: number
    centerLat?: number
    centerLng?: number
  }>(),
  {
    lat: null,
    lng: null,
    interactive: true,
    tooltip: '',
    zoom: 6,
    centerLat: DEFAULT_MAP_CENTER.lat,
    centerLng: DEFAULT_MAP_CENTER.lng,
  }
)

const emit = defineEmits<{
  pick: [lat: number, lng: number]
}>()

const containerEl = ref<HTMLElement | null>(null)

let map: LeafletMap | null = null
let marker: LeafletMarker | null = null
let resizeObserver: ResizeObserver | null = null
const refreshTimers: number[] = []

function hasValidCoords(lat: unknown, lng: unknown): lat is number {
  return (
    typeof lat === 'number' &&
    typeof lng === 'number' &&
    Number.isFinite(lat) &&
    Number.isFinite(lng)
  )
}

function shouldShowPin(): boolean {
  if (!hasValidCoords(props.lat, props.lng)) return false
  if (props.pinned === false) return false
  return true
}

function clearRefreshTimers() {
  while (refreshTimers.length) {
    window.clearTimeout(refreshTimers.pop())
  }
}

function refreshSize() {
  if (!map) return
  try {
    map.invalidateSize({ pan: false })
  } catch {
    /* map not ready */
  }
}

function scheduleSizeRefresh() {
  clearRefreshTimers()
  refreshSize()
  refreshTimers.push(window.setTimeout(refreshSize, 50))
  refreshTimers.push(window.setTimeout(refreshSize, 250))
  refreshTimers.push(window.setTimeout(refreshSize, 600))
}

function syncMarker(L: typeof import('leaflet')) {
  if (!map) return

  if (!shouldShowPin()) {
    if (marker) {
      marker.remove()
      marker = null
    }
    return
  }

  const lat = props.lat as number
  const lng = props.lng as number
  const icon = createMapPinIcon(L)

  if (marker) {
    marker.setLatLng([lat, lng])
    marker.setIcon(icon)
  } else {
    marker = L.marker([lat, lng], { icon, zIndexOffset: 1000 }).addTo(map)
  }

  if (props.tooltip) {
    marker.bindTooltip(props.tooltip, {
      permanent: false,
      direction: 'top',
      opacity: 0.95,
      offset: [0, -8],
      className: 'ss-map-tooltip',
    })
  } else {
    marker.unbindTooltip()
  }
}

async function initMap() {
  await nextTick()
  const el = containerEl.value
  if (!el || map) return

  const L = await import('leaflet')
  if (!containerEl.value || !containerEl.value.isConnected) return

  const startLat = shouldShowPin() ? (props.lat as number) : props.centerLat
  const startLng = shouldShowPin() ? (props.lng as number) : props.centerLng
  const startZoom = shouldShowPin() ? Math.max(props.zoom, 14) : props.zoom

  map = L.map(el, {
    zoomControl: false,
    scrollWheelZoom: true,
    attributionControl: true,
  })

  L.control.zoom({ position: 'bottomleft' }).addTo(map)

  L.tileLayer(OSM_TILE_URL, {
    attribution: OSM_ATTRIBUTION,
    maxZoom: 19,
  }).addTo(map)

  if (props.interactive) {
    map.on('click', (e: { latlng: { lat: number; lng: number } }) => {
      const { lat, lng } = e.latlng
      const roundedLat = Math.round(lat * 1e6) / 1e6
      const roundedLng = Math.round(lng * 1e6) / 1e6
      const currentZoom = map!.getZoom()
      const targetZoom = Number.isFinite(currentZoom) ? Math.max(currentZoom, 15) : 15
      try {
        map!.flyTo([lat, lng], targetZoom, { duration: 0.5 })
      } catch {
        map!.setView([lat, lng], targetZoom)
      }
      emit('pick', roundedLat, roundedLng)
    })
  }

  map.whenReady(() => {
    try {
      map!.setView([startLat, startLng], startZoom, { animate: false })
    } catch {
      /* ignore */
    }
    syncMarker(L)
    scheduleSizeRefresh()
  })

  resizeObserver = new ResizeObserver(() => refreshSize())
  resizeObserver.observe(el)
  // Also observe the outer wrapper — height often settles after the inner div mounts.
  const wrapper = el.parentElement
  if (wrapper) resizeObserver.observe(wrapper)
}

function destroyMap() {
  clearRefreshTimers()
  resizeObserver?.disconnect()
  resizeObserver = null
  marker = null
  if (map) {
    map.remove()
    map = null
  }
}

onMounted(() => {
  void initMap()
})

onUnmounted(() => {
  destroyMap()
})

watch(
  () => [props.lat, props.lng, props.pinned, props.tooltip, props.zoom] as const,
  async () => {
    if (!map) return
    const L = await import('leaflet')
    syncMarker(L)
    if (shouldShowPin() && props.lat != null && props.lng != null) {
      const rawZoom = map.getZoom()
      const zoom = Number.isFinite(rawZoom)
        ? Math.max(rawZoom, props.zoom >= 14 ? props.zoom : 14)
        : Math.max(props.zoom, 14)
      try {
        map.setView([props.lat, props.lng], zoom, { animate: false })
      } catch {
        /* ignore */
      }
    }
    scheduleSizeRefresh()
  }
)
</script>
