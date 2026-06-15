import { useEffect, useState } from 'react'
import { adminFetch } from '../auth'

const API = import.meta.env.VITE_API_URL || '/api'

const ACCEPTED_LABELS = new Set([
  'en réussite',
  'en reussite',
  'reussite',
  'success',
  'reuss',
  'accordé',
  'accorde',
])

const LEGACY_STATUS_MAP = {
  'accordé': 'En réussite',
  'accorde': 'En réussite',
  'refusé': 'À risque de décrochage',
  'refuse': 'À risque de décrochage',
  'refus': 'À risque de décrochage',
}

function normalizePrediction(prediction) {
  const value = String(prediction || '').trim()
  const key = value.toLowerCase()
  return LEGACY_STATUS_MAP[key] || value
}

function isAccepted(prediction) {
  return ACCEPTED_LABELS.has(String(prediction).toLowerCase())
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })
}

export default function AdminPredictions() {
  const [predictions, setPredictions] = useState(null)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  useEffect(() => {
    adminFetch(`${API}/admin/predictions?limit=100`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(setPredictions)
      .catch((err) => setError(err.message))
  }, [])

  if (error) {
    return (
      <div className="dash">
        <div className="empty">Erreur de chargement : {error}</div>
      </div>
    )
  }
  if (predictions === null) {
    return (
      <div className="dash">
        <div className="empty">Chargement...</div>
      </div>
    )
  }

  const filtered = predictions.filter((p) => {
    const matchQuery = query === '' || (p.applicant_name || '').toLowerCase().includes(query.toLowerCase())
    const normalizedPrediction = normalizePrediction(p.prediction)
    const matchStatus = statusFilter === 'all' || normalizedPrediction === statusFilter
    return matchQuery && matchStatus
  })

  return (
    <div className="dash">
      <div className="dash-header">
        <h1>Évaluations</h1>
        <p>Historique des évaluations. {filtered.length} résultat{filtered.length > 1 ? 's' : ''}.</p>
      </div>

      <div className="filters">
        <input
          type="search"
          placeholder="Rechercher par nom..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="search"
        />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="filter-select">
          <option value="all">Tous les statuts</option>
          <option value="En réussite">En réussite</option>
          <option value="À surveiller">À surveiller</option>
          <option value="À risque de décrochage">À risque de décrochage</option>
        </select>
      </div>

      <div className="dash-card no-pad">
        {filtered.length === 0 ? (
          <div className="empty">
            {predictions.length === 0
              ? "Aucune évaluation pour l'instant. Soumettez-en une depuis le formulaire."
              : 'Aucune évaluation ne correspond à votre recherche.'}
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>Élève</th>
                <th>Niveau</th>
                <th>Score</th>
                <th>Statut</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => {
                const normalizedPrediction = normalizePrediction(p.prediction)
                const accepted = isAccepted(normalizedPrediction)
                return (
                  <tr key={p.id}>
                    <td className="mono">#{p.id}</td>
                    <td>{p.applicant_name || <span className="muted">Anonyme</span>}</td>
                    <td>{p.features?.level !== undefined ? ['Primaire', 'Collège', 'Lycée', 'Supérieur'][p.features.level] : '—'}</td>
                    <td>
                      {p.score !== null && p.score !== undefined ? (
                        <div className="score-bar">
                          <span className="score-bar-fill" style={{ width: `${p.score}%` }} />
                          <span className="score-bar-text">{p.score}</span>
                        </div>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                    <td>
                      <span className={`pill ${accepted ? 'pill-ok' : 'pill-ko'}`}>
                        {normalizedPrediction}
                      </span>
                    </td>
                    <td className="muted">{formatDate(p.created_at)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
