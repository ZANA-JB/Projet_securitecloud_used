import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getToken, getUser, logout } from '../auth'

const API = import.meta.env.VITE_API_URL || '/api'

const SITUATIONS = [
  { label: 'Célibataire', value: 0 },
  { label: 'Marié(e)', value: 1 },
  { label: 'Divorcé(e)', value: 2 },
  { label: 'Veuf / Veuve', value: 3 },
]

const PROFESSIONS = [
  { label: 'Salarié(e)', value: 0 },
  { label: 'Indépendant(e) / Commerçant(e)', value: 1 },
  { label: 'Agriculteur / Éleveur', value: 2 },
  { label: 'Étudiant(e)', value: 3 },
  { label: 'Sans emploi', value: 4 },
]

const HISTORIQUE = [
  { label: 'Aucun crédit auparavant', value: 0 },
  { label: 'Crédit en cours', value: 1 },
  { label: 'Crédit remboursé sans incident', value: 2 },
  { label: 'Crédit avec retards', value: 3 },
]

export default function PublicForm() {
  const navigate = useNavigate()
  const user = getUser()
  const [step, setStep] = useState('form')
  const [health, setHealth] = useState('checking')
  const [form, setForm] = useState({
    nom: '',
    age: 30,
    situation: 1,
    profession: 0,
    revenu: 200000,
    montant: 500000,
    duree: 12,
    historique: 0,
  })
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => r.json())
      .then((d) => setHealth(d.status))
      .catch(() => setHealth('down'))
  }, [])

  const updateField = (key, value) => setForm((f) => ({ ...f, [key]: value }))

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setStep('loading')

    const features = [
      form.age,
      form.situation,
      form.profession,
      form.revenu / 1000,
      form.montant / 1000,
      form.duree,
      form.historique,
    ]

    try {
      const r = await fetch(`${API}/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({
          features,
          applicant_name: form.nom,
          amount: form.montant,
          duration_months: form.duree,
        }),
      })
      if (r.status === 401 || r.status === 403) {
        logout()
        navigate('/login', { replace: true })
        return
      }
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const data = await r.json()
      setResult(data)
      setStep('result')
    } catch (err) {
      setError(err.message)
      setStep('form')
    }
  }

  const reset = () => {
    setStep('form')
    setResult(null)
    setError(null)
  }

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="brand">
            <div className="brand-mark">μ</div>
            <div>
              <div className="brand-name">MicroScore</div>
              <div className="brand-sub">Évaluation de dossier de crédit</div>
            </div>
          </div>
          <div className="header-right">
            <div className={`health health-${health}`}>
              <span className="health-dot" />
              {health === 'ok' ? 'En ligne' : health === 'down' ? 'Indisponible' : 'Connexion...'}
            </div>
            {user?.role === 'admin' && (
              <Link to="/admin" className="admin-link">
                Espace admin →
              </Link>
            )}
            <div className="header-user">
              <span>{user?.name || user?.email}</span>
              <button type="button" onClick={handleLogout} className="header-logout">
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="main">
        {step === 'form' && (
          <FormPanel form={form} updateField={updateField} submit={submit} error={error} />
        )}
        {step === 'loading' && <LoadingPanel />}
        {step === 'result' && result && <ResultPanel form={form} result={result} reset={reset} />}
      </main>

      <footer className="footer">
        Démo pédagogique — Master IA 2iE — Les décisions de crédit réelles relèvent d'un comité humain.
      </footer>
    </div>
  )
}

function FormPanel({ form, updateField, submit, error }) {
  return (
    <form onSubmit={submit} className="card">
      <div className="card-header">
        <h1>Nouvelle demande de crédit</h1>
        <p>Renseignez les informations du demandeur pour obtenir une évaluation.</p>
      </div>

      <section className="section">
        <h2>Identité</h2>
        <div className="grid">
          <Field label="Nom complet">
            <input
              type="text"
              value={form.nom}
              onChange={(e) => updateField('nom', e.target.value)}
              placeholder="Ex. Aminata Ouédraogo"
              required
            />
          </Field>
          <Field label="Âge">
            <input
              type="number"
              min="18"
              max="80"
              value={form.age}
              onChange={(e) => updateField('age', Number(e.target.value))}
              required
            />
          </Field>
          <Select
            label="Situation familiale"
            value={form.situation}
            options={SITUATIONS}
            onChange={(v) => updateField('situation', v)}
          />
          <Select
            label="Profession"
            value={form.profession}
            options={PROFESSIONS}
            onChange={(v) => updateField('profession', v)}
          />
        </div>
      </section>

      <section className="section">
        <h2>Crédit demandé</h2>
        <div className="grid">
          <Field label="Revenu mensuel (FCFA)">
            <input
              type="number"
              min="0"
              step="10000"
              value={form.revenu}
              onChange={(e) => updateField('revenu', Number(e.target.value))}
              required
            />
          </Field>
          <Field label="Montant demandé (FCFA)">
            <input
              type="number"
              min="0"
              step="50000"
              value={form.montant}
              onChange={(e) => updateField('montant', Number(e.target.value))}
              required
            />
          </Field>
          <Field label="Durée souhaitée (mois)">
            <input
              type="number"
              min="3"
              max="60"
              value={form.duree}
              onChange={(e) => updateField('duree', Number(e.target.value))}
              required
            />
          </Field>
          <Select
            label="Historique de crédit"
            value={form.historique}
            options={HISTORIQUE}
            onChange={(v) => updateField('historique', v)}
          />
        </div>
      </section>

      {error && <div className="error">Erreur : {error}</div>}

      <div className="actions">
        <button type="submit" className="btn-primary">
          Évaluer la demande
        </button>
      </div>
    </form>
  )
}

function LoadingPanel() {
  return (
    <div className="card loading">
      <div className="spinner" />
      <h2>Analyse en cours</h2>
      <p>Évaluation du dossier basée sur l'historique et le profil du demandeur.</p>
    </div>
  )
}

function ResultPanel({ form, result, reset }) {
  const score = result.score ?? (result.proba ? Math.round(result.proba[result.proba.length - 1] * 1000) : null)
  const accepted = result.prediction === 'accordé' || result.prediction === 1 || (score !== null && score >= 600)
  const risque = score !== null ? (score >= 750 ? 'Faible' : score >= 500 ? 'Modéré' : 'Élevé') : '—'

  return (
    <div className="card result">
      <div className={`badge ${accepted ? 'badge-ok' : 'badge-ko'}`}>
        {accepted ? '✓ Dossier favorable' : '✗ Dossier défavorable'}
      </div>

      <h1>Évaluation pour {form.nom || 'le demandeur'}</h1>

      <div className="metrics">
        <Metric label="Score" value={score ?? '—'} suffix={score ? '/1000' : ''} />
        <Metric label="Risque" value={risque} />
        <Metric label="Montant" value={form.montant.toLocaleString('fr-FR')} suffix=" FCFA" />
        <Metric label="Durée" value={form.duree} suffix=" mois" />
      </div>

      <div className="recommendation">
        <h3>Recommandation</h3>
        <p>
          {accepted
            ? `Le profil et l'historique du demandeur sont compatibles avec le crédit demandé. Une vérification finale en comité reste recommandée.`
            : `Le profil présente des facteurs de risque significatifs. Envisager un montant inférieur, une garantie complémentaire, ou un refus argumenté.`}
        </p>
        <p className="note">
          Cette évaluation est une aide à la décision, pas une décision automatique. Le comité de crédit garde la responsabilité finale.
        </p>
      </div>

      <div className="actions">
        <button onClick={reset} className="btn-secondary">
          Nouvelle demande
        </button>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
    </label>
  )
}

function Select({ label, value, options, onChange }) {
  return (
    <Field label={label}>
      <select value={value} onChange={(e) => onChange(Number(e.target.value))}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </Field>
  )
}

function Metric({ label, value, suffix = '' }) {
  return (
    <div className="metric">
      <div className="metric-label">{label}</div>
      <div className="metric-value">
        {value}
        <span className="metric-suffix">{suffix}</span>
      </div>
    </div>
  )
}
