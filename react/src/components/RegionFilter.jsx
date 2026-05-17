import { useState } from 'react'
import { Map } from 'lucide-react'
import './RegionFilter.css'

export const GREEK_REGIONS = [
  { id: 'attica',    el: 'Αττική',                          en: 'Attica' },
  { id: 'c-mac',     el: 'Κεντρική Μακεδονία',              en: 'Central Macedonia' },
  { id: 'e-mac',     el: 'Ανατολική Μακεδονία & Θράκη',    en: 'Eastern Macedonia & Thrace' },
  { id: 'w-mac',     el: 'Δυτική Μακεδονία',                en: 'Western Macedonia' },
  { id: 'epirus',    el: 'Ήπειρος',                         en: 'Epirus' },
  { id: 'thessaly',  el: 'Θεσσαλία',                        en: 'Thessaly' },
  { id: 'c-greece',  el: 'Στερεά Ελλάδα',                   en: 'Central Greece' },
  { id: 'w-greece',  el: 'Δυτική Ελλάδα',                   en: 'Western Greece' },
  { id: 'peloponne', el: 'Πελοπόννησος',                    en: 'Peloponnese' },
  { id: 'ionian',    el: 'Ιόνια Νησιά',                     en: 'Ionian Islands' },
  { id: 'n-aegean',  el: 'Βόρειο Αιγαίο',                   en: 'Northern Aegean' },
  { id: 's-aegean',  el: 'Νότιο Αιγαίο',                    en: 'Southern Aegean' },
  { id: 'crete',     el: 'Κρήτη',                           en: 'Crete' },
]

// Keywords used to fuzzy-match OSM region strings to a standard region
const REGION_KEYWORDS = {
  attica:    ['attic', 'athens', 'αττικ', 'αθήνα', 'αθηνα'],
  'c-mac':   ['central mac', 'κεντρική μακ', 'thessaloniki', 'θεσσαλονίκη'],
  'e-mac':   ['eastern mac', 'east mac', 'thrace', 'θράκη', 'ανατολική μακ', 'kavala', 'drama'],
  'w-mac':   ['western mac', 'δυτική μακ', 'kozani', 'κοζάνη', 'kastoria'],
  epirus:    ['epirus', 'ήπειρ', 'ioannina', 'ιωάννιν', 'zagori', 'ζαγόρι'],
  thessaly:  ['thessal', 'θεσσαλ', 'larissa', 'λάρισ', 'volos', 'βόλος', 'meteora'],
  'c-greece':['central greece', 'στερεά', 'phocis', 'φωκίδα', 'delphi', 'δελφ', 'evia', 'εύβοια'],
  'w-greece':['western greece', 'δυτική ελλάδα', 'aetolia', 'αιτωλ', 'patras', 'πάτρα', 'achaia'],
  peloponne: ['peloponne', 'πελοπόννησ', 'sparta', 'σπάρτη', 'arcadia', 'αρκαδ', 'olympia'],
  ionian:    ['ionian', 'ιόνι', 'corfu', 'κέρκυρ', 'lefkada', 'kefalonia', 'zakynthos', 'ζάκυνθ'],
  'n-aegean':['north aegean', 'βόρειο αιγ', 'lesvos', 'λέσβ', 'chios', 'χίος', 'samos', 'σάμος'],
  's-aegean':['south aegean', 'νότιο αιγ', 'cyclades', 'κυκλάδ', 'dodecanese', 'δωδεκάν', 'rhodes', 'ρόδος', 'santorini', 'mykonos'],
  crete:     ['crete', 'κρήτη', 'κρητ', 'heraklion', 'ηράκλειο', 'chania', 'χανιά', 'rethymno'],
}

export function matchRegion(trailRegion) {
  if (!trailRegion) return null
  const low = trailRegion.toLowerCase()
  for (const [id, keywords] of Object.entries(REGION_KEYWORDS)) {
    if (keywords.some(k => low.includes(k))) return id
  }
  return null
}

export default function RegionFilter({ value, onChange, dark = false }) {
  const [open, setOpen] = useState(false)
  const selected = GREEK_REGIONS.find(r => r.id === value)

  return (
    <div className={`region-filter ${dark ? 'region-filter-dark' : ''}`}>
      <button className="region-trigger" onClick={() => setOpen(!open)}>
        <Map size={14} /> {selected ? selected.el : 'Όλη η Ελλάδα'}
        <span className="region-caret">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="region-dropdown">
          <button
            className={`region-option ${!value ? 'active' : ''}`}
            onClick={() => { onChange(null); setOpen(false) }}
          >
            Όλη η Ελλάδα <span className="region-en">All regions</span>
          </button>
          {GREEK_REGIONS.map(r => (
            <button
              key={r.id}
              className={`region-option ${value === r.id ? 'active' : ''}`}
              onClick={() => { onChange(r.id); setOpen(false) }}
            >
              {r.el} <span className="region-en">{r.en}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
