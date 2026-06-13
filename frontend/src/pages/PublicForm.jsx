import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getToken, getUser, logout } from '../auth'

const API = import.meta.env.VITE_API_URL || '/api'

const DEFAULT_SUBJECTS = [
  { label: 'Mathématiques', value: 0 },
  { label: 'Français', value: 1 },
  { label: 'Anglais', value: 2 },
  { label: 'Sciences', value: 3 },
  { label: 'Histoire', value: 4 },
  { label: 'Informatique', value: 5 },
]

export default function PublicForm() {
  const navigate = useNavigate()
  const user = getUser()
  const [step, setStep] = useState('form')
  const [health, setHealth] = useState('checking')
  const [fieldsApi, setFieldsApi] = useState(null)
  const [form, setForm] = useState({
    applicant_name: '',
    level: 2,
    main_subject: 0,
    average_grade: 12.0,
    attendance_rate: 90.0,
    study_hours_per_week: 5,
    resources_access: 1,
    last_exam_result: 0,
  })
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => r.json())
      .then((d) => setHealth(d.status))
      .catch(() => setHealth('down'))

    // Récupère la définition des champs depuis le backend (nommage canonique)
    fetch(`${API}/fields`)
      .then((r) => r.json())
      .then((d) => setFieldsApi(d))
      .catch(() => setFieldsApi(null))
  }, [])

  const updateField = (key, value) => setForm((f) => ({ ...f, [key]: value }))

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setStep('loading')

    try {
      const r = await fetch(`${API}/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify(form),
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
            <div className="brand-mark">E</div>
            <div>
              <div className="brand-name">EduScore</div>
              <div className="brand-sub">Évaluation du risque de décrochage scolaire</div>
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
          <FormPanel form={form} updateField={updateField} submit={submit} error={error} fieldsApi={fieldsApi} />
        )}
        {step === 'loading' && <LoadingPanel />}
        {step === 'result' && result && <ResultPanel form={form} result={result} reset={reset} />}
      </main>

      <footer className="footer">
        Démo pédagogique — Master IA 2iE — Cette évaluation reste indicative.
      </footer>
    </div>
  )
}

function FormPanel({ form, updateField, submit, error, fieldsApi }) {
  const LEVELS = [
    { label: 'Primaire', value: 0 },
    { label: 'Collège', value: 1 },
    { label: 'Lycée', value: 2 },
    { label: 'Supérieur', value: 3 },
  ]

  const SUBJECTS = fieldsApi?.main_subjects || DEFAULT_SUBJECTS

  return (
    <form onSubmit={submit} className="card">
      <div className="card-header">
        <h1>Évaluation scolaire</h1>
        <p>Renseignez le profil pour obtenir une prédiction de risque de décrochage.</p>
      </div>

      <section className="section">
        <h2>Informations</h2>
        <div className="grid">
          <Field label="Nom de l'élève">
            <input
              type="text"
              value={form.applicant_name}
              onChange={(e) => updateField('applicant_name', e.target.value)}
              placeholder="Ex. Aminata Ouédraogo"
            />
          </Field>

          <Select label="Niveau scolaire" value={form.level} options={LEVELS} onChange={(v) => updateField('level', v)} />

          <Select
            label="Filière / matière principale"
            value={form.main_subject}
            options={SUBJECTS}
            onChange={(v) => updateField('main_subject', v)}
          />

          <Field label="Note moyenne (sur 20)">
            <input
              type="number"
              min="0"
              max="20"
              step="0.1"
              value={form.average_grade}
              onChange={(e) => updateField('average_grade', Number(e.target.value))}
            />
          </Field>

          <Field label="Taux d'assiduité (%)">
            <input
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={form.attendance_rate}
              onChange={(e) => updateField('attendance_rate', Number(e.target.value))}
            />
          </Field>

          <Field label="Heures d'étude par semaine">
            <input
              type="number"
              min="0"
              max="80"
              value={form.study_hours_per_week}
              onChange={(e) => updateField('study_hours_per_week', Number(e.target.value))}
            />
          </Field>

          <Select
            label="Accès aux ressources (0=aucun,3=très bon)"
            value={form.resources_access}
            options={[{ label: '0', value: 0 }, { label: '1', value: 1 }, { label: '2', value: 2 }, { label: '3', value: 3 }]}
            onChange={(v) => updateField('resources_access', v)}
          />

          <Select
            label="Résultat dernier examen"
            value={form.last_exam_result}
            options={[{ label: 'Réussi', value: 0 }, { label: 'Échoué', value: 1 }, { label: "Non passé", value: 2 }]}
            onChange={(v) => updateField('last_exam_result', v)}
          />
        </div>
      </section>

      {error && <div className="error">Erreur : {error}</div>}

      <div className="actions">
        <button type="submit" className="btn-primary">
          Évaluer
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
      <p>Évaluation du profil pour estimer le risque de décrochage.</p>
    </div>
  )
}

function ResultPanel({ form, result, reset }) {
  const score = result.score ?? (result.proba ? Math.round(Math.max(...result.proba) * 100) : null)
  const success = String(result.prediction).toLowerCase().includes('réuss') || String(result.prediction).toLowerCase().includes('reuss')
  const risk = score !== null ? (score >= 75 ? 'Faible' : score >= 50 ? 'Modéré' : 'Élevé') : '—'

  return (
    <div className="card result">
      <div className={`badge ${success ? 'badge-ok' : 'badge-ko'}`}>
        {success ? 'Profil en réussite' : 'Profil à risque'}
      </div>

      <h1>Évaluation pour {form.applicant_name || 'l’élève'}</h1>

      <div className="metrics">
        <Metric label="Score" value={score ?? '—'} suffix={score ? '/100' : ''} />
        <Metric label="Risque" value={risk} />
        <Metric label="Niveau" value={['Primaire', 'Collège', 'Lycée', 'Supérieur'][form.level] || '—'} />
        <Metric label="Filière" value={DEFAULT_SUBJECTS.find((s) => s.value === form.main_subject)?.label || '—'} />
      </div>

      <div className="recommendation">
        <h3>Recommandation</h3>
        <p>
          {success
            ? `Le profil semble en réussite. Maintenir le suivi et encourager les bonnes pratiques.`
            : `Le profil montre des signaux de fragilité. Mettre en place un accompagnement ciblé (tutorat, ressources, suivi).`}
        </p>
        <p className="note">Cette évaluation est indicative et doit être complétée par un examen humain.</p>
      </div>

      <div className="actions">
        <button onClick={reset} className="btn-secondary">
          Nouvelle évaluation
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
