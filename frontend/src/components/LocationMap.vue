<template>
  <div class="ss-location-map relative isolate h-full min-h-0 w-full overflow-hidden bg-slate-100">
    <div ref="containerEl" class="absolute inset-0 z-0 h-full w-full" />
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import L, { type Map as LeafletMap, type Marker as LeafletMarker } from 'leaflet'
import {
  addBasemapTiles,
  createMapPinIcon,
  DEFAULT_MAP_CENTER,
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
let resizeDebounceTimer: number | null = null
const refreshTimers: number[] = []
/** Coords we just emitted from a click — watcher should only sync the pin, not re-pan. */
let lastPicked: { lat: number; lng: number } | null = null

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

function samePick(lat: number, lng: number) {
  return (
    lastPicked != null &&
    Math.abs(lastPicked.lat - lat) < 1e-7 &&
    Math.abs(lastPicked.lng - lng) < 1e-7
  )
}

function clearRefreshTimers() {
  while (refreshTimers.length) {
    window.clearTimeout(refreshTimers.pop())
  }
}

function refreshSize() {
  if (!map) return
  const container = map.getContainer()
  if (
    container.classList.contains('leaflet-dragging') ||
    container.classList.contains('leaflet-zoom-anim')
  ) {
    return
  }
  try {
    map.invalidateSize({ pan: false, debounceMoveend: true })
  } catch {
    /* map not ready */
  }
}

function scheduleSizeRefresh() {
  clearRefreshTimers()
  refreshTimers.push(window.setTimeout(refreshSize, 100))
  refreshTimers.push(window.setTimeout(refreshSize, 400))
}

function onResizeObserved() {
  if (resizeDebounceTimer != null) window.clearTimeout(resizeDebounceTimer)
  resizeDebounceTimer = window.setTimeout(() => {
    resizeDebounceTimer = null
    refreshSize()
  }, 150)
}

function syncMarker() {
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
  if (!el.isConnected) return

  if (el.clientWidth === 0 || el.clientHeight === 0) {
    await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
  }

  const startLat = shouldShowPin() ? (props.lat as number) : props.centerLat
  const startLng = shouldShowPin() ? (props.lng as number) : props.centerLng
  const startZoom = shouldShowPin() ? Math.max(props.zoom, 14) : props.zoom

  map = L.map(el, {
    zoomControl: false,
    scrollWheelZoom: true,
    attributionControl: true,
    wheelPxPerZoomLevel: 120,
    wheelDebounceTime: 40,
    // Integer zoom — raster tiles are most reliable at whole levels
    zoomSnap: 1,
    zoomDelta: 1,
    fadeAnimation: true,
    zoomAnimation: true,
    markerZoomAnimation: true,
    inertia: true,
  }).setView([startLat, startLng], startZoom)

  L.control.zoom({ position: 'bottomleft' }).addTo(map)

  addBasemapTiles(map, L)

  if (props.interactive) {
    map.on('click', (e) => {
      const { lat, lng } = e.latlng
      const roundedLat = Math.round(lat * 1e6) / 1e6
      const roundedLng = Math.round(lng * 1e6) / 1e6
      lastPicked = { lat: roundedLat, lng: roundedLng }
      // Pin only — do not setView/zoom here (parent will update lat/lng; watcher syncs marker).
      if (marker) {
        marker.setLatLng([roundedLat, roundedLng])
      } else {
        marker = L.marker([roundedLat, roundedLng], {
          icon: createMapPinIcon(L),
          zIndexOffset: 1000,
        }).addTo(map!)
      }
      emit('pick', roundedLat, roundedLng)
    })
  }

  syncMarker()
  scheduleSizeRefresh()

  resizeObserver = new ResizeObserver(onResizeObserved)
  resizeObserver.observe(el)
  const wrapper = el.parentElement
  if (wrapper) resizeObserver.observe(wrapper)
}

function destroyMap() {
  clearRefreshTimers()
  if (resizeDebounceTimer != null) {
    window.clearTimeout(resizeDebounceTimer)
    resizeDebounceTimer = null
  }
  resizeObserver?.disconnect()
  resizeObserver = null
  marker = null
  lastPicked = null
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
  () => [props.lat, props.lng, props.pinned, props.tooltip] as const,
  () => {
    if (!map) return
    syncMarker()
    if (!shouldShowPin() || props.lat == null || props.lng == null) return
    // Skip re-pan when this update came from our own click.
    if (samePick(props.lat, props.lng)) return
    lastPicked = null
    // External coord change (e.g. load existing job) — gentle recenter, no zoom fight.
    map.panTo([props.lat, props.lng], { animate: true, duration: 0.2 })
  }
)
</script>
