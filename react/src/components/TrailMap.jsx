import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix Leaflet default icon path issue with Vite
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const SCORE_COLOR = (score) => score >= 60 ? '#2d8a4e' : score >= 40 ? '#d4a017' : '#c53030'

function makeIcon(color) {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:14px;height:14px;border-radius:50%;
      background:${color};border:2px solid #fff;
      box-shadow:0 1px 4px rgba(0,0,0,.4)
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })
}

export default function TrailMap({ trails = [], pois = [], height = 460, dark = false }) {
  if (!trails.length && !pois.length) return <div style={{ height, background: dark ? '#1a1a2e' : '#eee', borderRadius: 12 }} />

  const points = trails.length ? trails : pois
  const center = [
    points.reduce((s, p) => s + p.lat, 0) / points.length,
    points.reduce((s, p) => s + p.lon, 0) / points.length,
  ]
  const zoom = trails.length > 1 ? 7 : 12

  return (
    <MapContainer center={center} zoom={zoom} style={{ height, borderRadius: 12, zIndex: 0 }}>
      {dark ? (
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
      ) : (
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
      )}
      {trails.map((t, i) => {
        const score = t._sustainability?.score || 0
        return (
          <Marker key={i} position={[t.lat, t.lon]} icon={makeIcon(SCORE_COLOR(score))}>
            <Popup>
              <strong>{t.name}</strong><br />
              {t.region}<br />
              Difficulty: {t.difficulty}<br />
              Sustainability: {score}/100
            </Popup>
          </Marker>
        )
      })}
      {pois.map((p, i) => (
        <Marker key={`poi-${i}`} position={[p.lat, p.lon]} icon={makeIcon('#555')}>
          <Popup>{p.emoji} <strong>{p.name}</strong><br />{p.category}</Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
