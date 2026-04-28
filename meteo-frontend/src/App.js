import { useState, useEffect } from "react";
import axios from "axios";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";

const API = "http://127.0.0.1:8000/api";

const COULEURS = {
  "Akwa": "#E05C5C", "Bonanjo": "#2E86C1", "Deido": "#27AE60",
  "Bepanda": "#E67E22", "Makepe": "#8E44AD", "New Bell": "#F39C12",
  "Bonapriso": "#16A085", "Logbaba": "#C0392B", "Cite SIC": "#2980B9",
  "Kotto": "#D35400"
};

const QUARTIERS = [
  { id: "SENSOR_AKWA",      nom: "Akwa",      lat: 4.0511, lon: 9.7085 },
  { id: "SENSOR_BONANJO",   nom: "Bonanjo",   lat: 4.0469, lon: 9.6966 },
  { id: "SENSOR_DEIDO",     nom: "Deido",     lat: 4.0631, lon: 9.7192 },
  { id: "SENSOR_BEPANDA",   nom: "Bepanda",   lat: 4.0756, lon: 9.7300 },
  { id: "SENSOR_MAKEPE",    nom: "Makepe",    lat: 4.0850, lon: 9.7450 },
  { id: "SENSOR_NEWBELL",   nom: "New Bell",  lat: 4.0600, lon: 9.7100 },
  { id: "SENSOR_BONAPRISO", nom: "Bonapriso", lat: 4.0420, lon: 9.7020 },
  { id: "SENSOR_LOGBABA",   nom: "Logbaba",   lat: 4.0300, lon: 9.7600 },
  { id: "SENSOR_CITE_SIC",  nom: "Cite SIC",  lat: 4.0700, lon: 9.7250 },
  { id: "SENSOR_KOTTO",     nom: "Kotto",     lat: 4.0900, lon: 9.7550 },
];

// ─── KPI Card ───
function KPICard({ titre, valeur, unite, couleur, icon }) {
  return (
    <div style={{
      background: "#fff", borderRadius: 12, padding: "18px 24px",
      boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
      borderLeft: `5px solid ${couleur}`, minWidth: 160, flex: 1
    }}>
      <div style={{ fontSize: 12, color: "#7F8C8D", marginBottom: 4 }}>{icon} {titre}</div>
      <div style={{ fontSize: 26, fontWeight: "bold", color: "#2C3E50" }}>
        {valeur !== null ? `${valeur}${unite}` : "—"}
      </div>
    </div>
  );
}

// ─── Notification ───
function Notif({ message, type }) {
  if (!message) return null;
  const bg = type === "success" ? "#27AE60" : "#E05C5C";
  return (
    <div style={{
      position: "fixed", top: 80, right: 24, background: bg,
      color: "#fff", borderRadius: 10, padding: "12px 24px",
      boxShadow: "0 4px 16px rgba(0,0,0,0.2)", zIndex: 1000,
      fontSize: 14, fontWeight: 600
    }}>
      {type === "success" ? "✅ " : "❌ "}{message}
    </div>
  );
}

// ─── Console CQL ───
function ConsoleCQL() {
  const [query, setQuery] = useState(
    "SELECT sensor_id, quartier, temperature FROM mesures_capteurs WHERE sensor_id = 'SENSOR_AKWA' AND date = '2026-04-11' LIMIT 10"
  );
  const [resultats, setResultats] = useState(null);
  const [colonnes, setColonnes]   = useState([]);
  const [erreur, setErreur]       = useState(null);
  const [loading, setLoading]     = useState(false);

  const SUGGESTIONS = [
    { label: "Mesures Akwa",        query: "SELECT sensor_id, quartier, temperature, humidite FROM mesures_capteurs WHERE sensor_id = 'SENSOR_AKWA' AND date = '2026-04-11' LIMIT 20" },
    { label: "Compter mesures",     query: "SELECT COUNT(*) FROM mesures_capteurs WHERE sensor_id = 'SENSOR_BONANJO' AND date = '2026-04-11'" },
    { label: "Tous les capteurs",   query: "SELECT * FROM capteurs" },
    { label: "Stats Deido",         query: "SELECT sensor_id, MAX(temperature), MIN(temperature) FROM mesures_capteurs WHERE sensor_id = 'SENSOR_DEIDO' AND date = '2026-04-11'" },
    { label: "Keyspaces",           query: "DESCRIBE KEYSPACES" },
  ];

  const executer = async () => {
    setLoading(true); setErreur(null); setResultats(null);
    try {
      const res = await axios.post(`${API}/cql/`, { query });
      setColonnes(res.data.colonnes);
      setResultats(res.data.resultats);
    } catch (e) {
      setErreur(e.response?.data?.detail || "Erreur inconnue");
    } finally { setLoading(false); }
  };

  return (
    <div style={{ background: "#1A1A2E", borderRadius: 12, padding: 24 }}>
      <div style={{ display: "flex", alignItems: "center", marginBottom: 16, gap: 10 }}>
        <span style={{ fontSize: 20 }}>⌨️</span>
        <h3 style={{ color: "#E0E0E0", margin: 0, fontSize: 16 }}>Console CQL — Apache Cassandra</h3>
        <span style={{ marginLeft: "auto", background: "#27AE60", color: "#fff", padding: "2px 10px", borderRadius: 20, fontSize: 11 }}>
          SELECT uniquement
        </span>
      </div>

      <div style={{ marginBottom: 12 }}>
        <div style={{ color: "#7F8C8D", fontSize: 12, marginBottom: 8 }}>Requêtes suggérées :</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {SUGGESTIONS.map((s, i) => (
            <button key={i} onClick={() => setQuery(s.query)} style={{
              background: "#16213E", color: "#A0AEC0",
              border: "1px solid #2D3748", borderRadius: 6,
              padding: "5px 12px", fontSize: 11, cursor: "pointer"
            }}>{s.label}</button>
          ))}
        </div>
      </div>

      <textarea value={query} onChange={e => setQuery(e.target.value)} rows={4} style={{
        width: "100%", background: "#16213E", color: "#00FF88",
        border: "1px solid #2D3748", borderRadius: 8, padding: 14,
        fontFamily: "Courier New, monospace", fontSize: 13,
        resize: "vertical", outline: "none", boxSizing: "border-box"
      }} />

      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 12 }}>
        <button onClick={executer} disabled={loading} style={{
          background: loading ? "#555" : "#2E86C1", color: "#fff",
          border: "none", borderRadius: 8, padding: "10px 28px",
          fontSize: 14, fontWeight: "bold", cursor: loading ? "not-allowed" : "pointer"
        }}>
          {loading ? "⏳ Exécution..." : "▶ Exécuter"}
        </button>
        <button onClick={() => { setQuery(""); setResultats(null); setErreur(null); }} style={{
          background: "transparent", color: "#7F8C8D",
          border: "1px solid #2D3748", borderRadius: 8,
          padding: "10px 20px", fontSize: 14, cursor: "pointer"
        }}>Effacer</button>
        {resultats && <span style={{ color: "#27AE60", fontSize: 13 }}>✓ {resultats.length} ligne(s)</span>}
      </div>

      {erreur && (
        <div style={{ marginTop: 12, background: "#2D1B1B", border: "1px solid #E05C5C", borderRadius: 8, padding: 12, color: "#E05C5C", fontSize: 13, fontFamily: "Courier New" }}>
          ❌ {erreur}
        </div>
      )}

      {resultats && resultats.length > 0 && (
        <div style={{ marginTop: 16, overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, color: "#E0E0E0" }}>
            <thead>
              <tr>
                {colonnes.map(col => (
                  <th key={col} style={{ background: "#0F3460", padding: "8px 12px", textAlign: "left", color: "#00FF88", borderBottom: "2px solid #2D3748" }}>
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {resultats.slice(0, 100).map((row, i) => (
                <tr key={i} style={{ background: i % 2 === 0 ? "#16213E" : "#1A1A2E" }}>
                  {colonnes.map(col => (
                    <td key={col} style={{ padding: "7px 12px", borderBottom: "1px solid #2D3748", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {String(row[col] ?? "")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {resultats.length > 100 && (
            <div style={{ color: "#7F8C8D", fontSize: 12, marginTop: 8, textAlign: "center" }}>
              Affichage limité à 100 lignes sur {resultats.length}
            </div>
          )}
        </div>
      )}
      {resultats && resultats.length === 0 && (
        <div style={{ color: "#7F8C8D", marginTop: 12, fontSize: 13 }}>Aucun résultat retourné.</div>
      )}
    </div>
  );
}

// ─── Gestion Capteurs ───
function GestionCapteurs({ notifier }) {
  const [capteurs, setCapteurs] = useState([]);
  const [loading, setLoading]   = useState(false);
  const [form, setForm]         = useState({ sensor_id: "", quartier: "", latitude: "", longitude: "", actif: true });
  const [showForm, setShowForm] = useState(false);

  const charger = async () => {
    try {
      const res = await axios.get(`${API}/capteurs/`);
      setCapteurs(res.data);
    } catch {}
  };

  useEffect(() => { charger(); }, []);

  const creer = async () => {
    if (!form.sensor_id || !form.quartier) return notifier("Remplissez tous les champs", "error");
    setLoading(true);
    try {
      await axios.post(`${API}/capteurs/`, {
        ...form,
        latitude:  parseFloat(form.latitude),
        longitude: parseFloat(form.longitude)
      });
      notifier("Capteur créé avec succès !", "success");
      setShowForm(false);
      setForm({ sensor_id: "", quartier: "", latitude: "", longitude: "", actif: true });
      charger();
    } catch (e) {
      notifier(e.response?.data?.detail || "Erreur création", "error");
    } finally { setLoading(false); }
  };

  const toggleActif = async (sensor_id, actif) => {
    try {
      await axios.put(`${API}/capteurs/${sensor_id}?actif=${!actif}`);
      notifier(`Capteur ${!actif ? "activé" : "désactivé"}`, "success");
      charger();
    } catch { notifier("Erreur mise à jour", "error"); }
  };

  const supprimer = async (sensor_id) => {
    if (!window.confirm(`Supprimer ${sensor_id} ?`)) return;
    try {
      await axios.delete(`${API}/capteurs/${sensor_id}`);
      notifier("Capteur supprimé", "success");
      charger();
    } catch { notifier("Erreur suppression", "error"); }
  };

  const selectionnerQuartier = (q) => {
    setForm({ ...form, sensor_id: `SENSOR_${q.nom.toUpperCase().replace(" ", "_")}`, quartier: q.nom, latitude: q.lat, longitude: q.lon });
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h3 style={{ margin: 0, color: "#2C3E50" }}>📡 Gestion des capteurs ({capteurs.length})</h3>
        <button onClick={() => setShowForm(!showForm)} style={{
          background: "#27AE60", color: "#fff", border: "none",
          borderRadius: 8, padding: "10px 20px", cursor: "pointer",
          fontSize: 14, fontWeight: "bold"
        }}>
          {showForm ? "✕ Annuler" : "+ Nouveau capteur"}
        </button>
      </div>

      {/* Formulaire création */}
      {showForm && (
        <div style={{ background: "#F8FAFC", borderRadius: 12, padding: 24, marginBottom: 24, border: "1px solid #E2E8F0" }}>
          <h4 style={{ margin: "0 0 16px", color: "#2C3E50" }}>Nouveau capteur</h4>

          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, color: "#7F8C8D", marginBottom: 6 }}>Quartier prédéfini (auto-remplit les coordonnées) :</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {QUARTIERS.map(q => (
                <button key={q.id} onClick={() => selectionnerQuartier(q)} style={{
                  background: form.quartier === q.nom ? COULEURS[q.nom] : "#E2E8F0",
                  color: form.quartier === q.nom ? "#fff" : "#2C3E50",
                  border: "none", borderRadius: 6, padding: "5px 12px",
                  cursor: "pointer", fontSize: 12, fontWeight: 600
                }}>{q.nom}</button>
              ))}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            {[
              { label: "ID Capteur", key: "sensor_id", placeholder: "Ex: SENSOR_AKWA" },
              { label: "Quartier",   key: "quartier",   placeholder: "Ex: Akwa" },
              { label: "Latitude",   key: "latitude",   placeholder: "Ex: 4.0511" },
              { label: "Longitude",  key: "longitude",  placeholder: "Ex: 9.7085" },
            ].map(f => (
              <div key={f.key}>
                <div style={{ fontSize: 12, color: "#7F8C8D", marginBottom: 4 }}>{f.label}</div>
                <input value={form[f.key]} onChange={e => setForm({ ...form, [f.key]: e.target.value })}
                  placeholder={f.placeholder} style={{
                    width: "100%", padding: "9px 12px", borderRadius: 8,
                    border: "1px solid #CBD5E0", fontSize: 13, outline: "none",
                    boxSizing: "border-box"
                  }} />
              </div>
            ))}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 16 }}>
            <button onClick={creer} disabled={loading} style={{
              background: loading ? "#aaa" : "#2E86C1", color: "#fff",
              border: "none", borderRadius: 8, padding: "10px 24px",
              fontSize: 14, fontWeight: "bold", cursor: "pointer"
            }}>
              {loading ? "Création..." : "✓ Créer le capteur"}
            </button>
          </div>
        </div>
      )}

      {/* Tableau capteurs */}
      <div style={{ background: "#fff", borderRadius: 12, overflow: "hidden", boxShadow: "0 2px 12px rgba(0,0,0,0.08)" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "#1A3A5C" }}>
              {["Capteur", "Quartier", "Latitude", "Longitude", "Statut", "Actions"].map(h => (
                <th key={h} style={{ color: "#fff", padding: "12px 16px", textAlign: "left", fontWeight: 600 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {capteurs.map((c, i) => (
              <tr key={i} style={{ background: i % 2 === 0 ? "#F8FAFC" : "#fff" }}>
                <td style={{ padding: "10px 16px", fontFamily: "monospace", fontSize: 12, color: "#2E86C1", fontWeight: 600 }}>{c.sensor_id}</td>
                <td style={{ padding: "10px 16px" }}>
                  <span style={{ background: COULEURS[c.quartier] || "#ccc", color: "#fff", borderRadius: 12, padding: "3px 10px", fontSize: 11, fontWeight: 600 }}>
                    {c.quartier}
                  </span>
                </td>
                <td style={{ padding: "10px 16px", color: "#7F8C8D", fontSize: 12 }}>{c.latitude}</td>
                <td style={{ padding: "10px 16px", color: "#7F8C8D", fontSize: 12 }}>{c.longitude}</td>
                <td style={{ padding: "10px 16px" }}>
                  <span style={{
                    background: c.actif ? "#D4EDDA" : "#F8D7DA",
                    color: c.actif ? "#155724" : "#721C24",
                    borderRadius: 12, padding: "3px 10px", fontSize: 11, fontWeight: 600
                  }}>
                    {c.actif ? "● Actif" : "○ Inactif"}
                  </span>
                </td>
                <td style={{ padding: "10px 16px" }}>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button onClick={() => toggleActif(c.sensor_id, c.actif)} style={{
                      background: c.actif ? "#E67E22" : "#27AE60",
                      color: "#fff", border: "none", borderRadius: 6,
                      padding: "5px 12px", fontSize: 11, cursor: "pointer", fontWeight: 600
                    }}>
                      {c.actif ? "Désactiver" : "Activer"}
                    </button>
                    <button onClick={() => supprimer(c.sensor_id)} style={{
                      background: "#E05C5C", color: "#fff", border: "none",
                      borderRadius: 6, padding: "5px 12px", fontSize: 11,
                      cursor: "pointer", fontWeight: 600
                    }}>Supprimer</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Insertion manuelle ───
function InsertionManuelle({ notifier }) {
  const [form, setForm] = useState({
    sensor_id: "SENSOR_AKWA", quartier: "Akwa",
    temperature: "", humidite: "", pression: ""
  });
  const [loading, setLoading]   = useState(false);
  const [historique, setHistorique] = useState([]);

  const selectionner = (q) => setForm({ ...form, sensor_id: q.id, quartier: q.nom });

  const inserer = async () => {
    if (!form.temperature || !form.humidite || !form.pression)
      return notifier("Remplissez tous les champs numériques", "error");

    const temp = parseFloat(form.temperature);
    const hum  = parseFloat(form.humidite);
    const pres = parseFloat(form.pression);

    if (temp < 0 || temp > 60)  return notifier("Température invalide (0-60°C)", "error");
    if (hum < 0  || hum > 100)  return notifier("Humidité invalide (0-100%)", "error");
    if (pres < 900 || pres > 1100) return notifier("Pression invalide (900-1100 hPa)", "error");

    setLoading(true);
    try {
      await axios.post(`${API}/mesures/`, {
        sensor_id:   form.sensor_id,
        quartier:    form.quartier,
        temperature: temp,
        humidite:    hum,
        pression:    pres
      });
      const entry = { ...form, temperature: temp, humidite: hum, pression: pres, timestamp: new Date().toLocaleTimeString() };
      setHistorique(prev => [entry, ...prev].slice(0, 10));
      notifier(`Mesure insérée pour ${form.quartier} !`, "success");
      setForm({ ...form, temperature: "", humidite: "", pression: "" });
    } catch (e) {
      notifier(e.response?.data?.detail || "Erreur insertion", "error");
    } finally { setLoading(false); }
  };

  const genererAleatoire = () => {
    const q = QUARTIERS[Math.floor(Math.random() * QUARTIERS.length)];
    setForm({
      sensor_id:   q.id,
      quartier:    q.nom,
      temperature: (24 + Math.random() * 11).toFixed(1),
      humidite:    (60 + Math.random() * 35).toFixed(1),
      pression:    (1008 + Math.random() * 7).toFixed(1)
    });
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>

      {/* Formulaire */}
      <div style={{ background: "#fff", borderRadius: 12, padding: 24, boxShadow: "0 2px 12px rgba(0,0,0,0.08)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h3 style={{ margin: 0, color: "#2C3E50", fontSize: 15 }}>📝 Insertion manuelle</h3>
          <button onClick={genererAleatoire} style={{
            background: "#F0F4F8", color: "#2E86C1", border: "1px solid #CBD5E0",
            borderRadius: 8, padding: "6px 14px", cursor: "pointer", fontSize: 12, fontWeight: 600
          }}>🎲 Aléatoire</button>
        </div>

        {/* Sélection capteur */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 12, color: "#7F8C8D", marginBottom: 8 }}>Capteur cible :</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {QUARTIERS.map(q => (
              <button key={q.id} onClick={() => selectionner(q)} style={{
                background: form.sensor_id === q.id ? COULEURS[q.nom] : "#F0F4F8",
                color: form.sensor_id === q.id ? "#fff" : "#2C3E50",
                border: "none", borderRadius: 6, padding: "5px 10px",
                cursor: "pointer", fontSize: 11, fontWeight: 600
              }}>{q.nom}</button>
            ))}
          </div>
        </div>

        <div style={{ background: "#F8FAFC", borderRadius: 8, padding: "10px 14px", marginBottom: 16, fontSize: 12 }}>
          <span style={{ color: "#7F8C8D" }}>Capteur sélectionné : </span>
          <span style={{ fontWeight: 700, color: COULEURS[form.quartier] || "#2C3E50" }}>
            {form.sensor_id} — {form.quartier}
          </span>
        </div>

        {/* Champs mesures */}
        {[
          { label: "Température (°C)", key: "temperature", placeholder: "Ex: 29.5", min: "0", max: "60", icon: "🌡️" },
          { label: "Humidité (%)",     key: "humidite",    placeholder: "Ex: 78.2", min: "0", max: "100", icon: "💧" },
          { label: "Pression (hPa)",   key: "pression",    placeholder: "Ex: 1011.3", min: "900", max: "1100", icon: "📊" },
        ].map(f => (
          <div key={f.key} style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 12, color: "#7F8C8D", marginBottom: 5 }}>{f.icon} {f.label}</div>
            <input
              type="number" value={form[f.key]}
              onChange={e => setForm({ ...form, [f.key]: e.target.value })}
              placeholder={f.placeholder} min={f.min} max={f.max} step="0.1"
              style={{
                width: "100%", padding: "10px 14px", borderRadius: 8,
                border: "1px solid #CBD5E0", fontSize: 14, outline: "none",
                boxSizing: "border-box", transition: "border 0.2s"
              }}
            />
          </div>
        ))}

        <button onClick={inserer} disabled={loading} style={{
          width: "100%", background: loading ? "#aaa" : "#1A3A5C",
          color: "#fff", border: "none", borderRadius: 10,
          padding: "13px", fontSize: 15, fontWeight: "bold",
          cursor: loading ? "not-allowed" : "pointer", marginTop: 4
        }}>
          {loading ? "⏳ Insertion..." : "⬆️ Insérer la mesure"}
        </button>
      </div>

      {/* Historique */}
      <div style={{ background: "#fff", borderRadius: 12, padding: 24, boxShadow: "0 2px 12px rgba(0,0,0,0.08)" }}>
        <h3 style={{ margin: "0 0 16px", color: "#2C3E50", fontSize: 15 }}>🕐 Historique des insertions</h3>
        {historique.length === 0 ? (
          <div style={{ color: "#BDC3C7", textAlign: "center", paddingTop: 40, fontSize: 13 }}>
            Aucune insertion encore effectuée
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {historique.map((h, i) => (
              <div key={i} style={{
                background: i === 0 ? "#F0FFF4" : "#F8FAFC",
                borderRadius: 10, padding: "12px 16px",
                border: i === 0 ? "1px solid #27AE60" : "1px solid #E2E8F0"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span style={{ fontWeight: 700, color: COULEURS[h.quartier] || "#2C3E50", fontSize: 13 }}>
                    {h.quartier}
                  </span>
                  <span style={{ color: "#7F8C8D", fontSize: 11 }}>{h.timestamp}</span>
                </div>
                <div style={{ display: "flex", gap: 16, fontSize: 12 }}>
                  <span style={{ color: "#E05C5C" }}>🌡️ {h.temperature}°C</span>
                  <span style={{ color: "#2E86C1" }}>💧 {h.humidite}%</span>
                  <span style={{ color: "#27AE60" }}>📊 {h.pression} hPa</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── App principale ───
export default function App() {
  const [stats, setStats]           = useState([]);
  const [mesures, setMesures]       = useState([]);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [activeTab, setActiveTab]   = useState("dashboard");
  const [notif, setNotif]           = useState({ message: null, type: null });

  const notifier = (message, type) => {
    setNotif({ message, type });
    setTimeout(() => setNotif({ message: null, type: null }), 3000);
  };

  const chargerDonnees = async () => {
    try {
      const capteursRes = await axios.get(`${API}/capteurs/`);
      const statsData = await Promise.all(
        capteursRes.data.map(async c => {
          try {
            const s = await axios.get(`${API}/mesures/${c.sensor_id}/stats`);
            return { ...c, ...s.data };
          } catch { return c; }
        })
      );
      setStats(statsData.filter(s => s.nb_mesures));

      const capteurIds = ["SENSOR_AKWA", "SENSOR_BONANJO", "SENSOR_DEIDO", "SENSOR_BEPANDA", "SENSOR_MAKEPE"];
      const mesuresData = [];
      for (const sensor of capteurIds) {
        try {
          const res = await axios.get(`${API}/mesures/${sensor}?limit=20`);
          mesuresData.push(...res.data);
        } catch {}
      }
      mesuresData.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      setMesures(mesuresData.slice(0, 50));
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    chargerDonnees();
    const interval = setInterval(chargerDonnees, 30000);
    return () => clearInterval(interval);
  }, []);

  const tempMoy     = stats.length ? (stats.reduce((s, c) => s + (c.temperature?.moy || 0), 0) / stats.length).toFixed(1) : null;
  const humMoy      = stats.length ? (stats.reduce((s, c) => s + (c.humidite?.moy || 0), 0) / stats.length).toFixed(1) : null;
  const totalMesures = stats.reduce((s, c) => s + (c.nb_mesures || 0), 0);
  const dataBarres  = stats.map(s => ({ quartier: s.quartier, temperature: parseFloat(s.temperature?.moy?.toFixed(1)), humidite: parseFloat(s.humidite?.moy?.toFixed(1)) }));
  const dataCourbe  = mesures.slice(0, 30).reverse().map(m => ({ time: new Date(m.timestamp).toLocaleTimeString(), [m.quartier]: parseFloat(m.temperature) }));

  const TABS = [
    { id: "dashboard",  label: "📊 Dashboard" },
    { id: "mesures",    label: "📋 Mesures" },
    { id: "insertion",  label: "📝 Insertion" },
    { id: "capteurs",   label: "📡 Capteurs" },
    { id: "cql",        label: "⌨️ Console CQL" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#F0F4F8", fontFamily: "'Segoe UI', sans-serif" }}>
      <Notif message={notif.message} type={notif.type} />

      {/* Header */}
      <div style={{
        background: "linear-gradient(135deg, #1A3A5C 0%, #2E86C1 100%)",
        padding: "0 32px", display: "flex", alignItems: "center",
        justifyContent: "space-between", boxShadow: "0 2px 12px rgba(0,0,0,0.15)", height: 64
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 28 }}>🌡️</span>
          <div>
            <div style={{ color: "#fff", fontWeight: "bold", fontSize: 18 }}>Surveillance Météo IoT</div>
            <div style={{ color: "#BDC3C7", fontSize: 11 }}>Douala, Cameroun — Cassandra 5.0.6 — Cluster 3 nœuds</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {TABS.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
              background: activeTab === tab.id ? "rgba(255,255,255,0.2)" : "transparent",
              color: "#fff", border: "1px solid rgba(255,255,255,0.3)",
              borderRadius: 8, padding: "7px 16px", cursor: "pointer",
              fontSize: 12, fontWeight: activeTab === tab.id ? "bold" : "normal"
            }}>{tab.label}</button>
          ))}
        </div>
        <div style={{ color: "#BDC3C7", fontSize: 12, display: "flex", alignItems: "center", gap: 8 }}>
          {lastUpdate ? `🕐 ${lastUpdate}` : "Chargement..."}
          <button onClick={chargerDonnees} style={{
            background: "rgba(255,255,255,0.1)", color: "#fff",
            border: "none", borderRadius: 6, padding: "4px 10px",
            cursor: "pointer", fontSize: 12
          }}>🔄</button>
        </div>
      </div>

      <div style={{ padding: 24 }}>

        {/* ── DASHBOARD ── */}
        {activeTab === "dashboard" && (
          <>
            <div style={{ display: "flex", gap: 16, marginBottom: 24, flexWrap: "wrap" }}>
              <KPICard titre="Température moyenne" valeur={tempMoy}  unite="°C" couleur="#E05C5C" icon="🌡️" />
              <KPICard titre="Humidité moyenne"    valeur={humMoy}   unite="%" couleur="#2E86C1"  icon="💧" />
              <KPICard titre="Total mesures"       valeur={totalMesures.toLocaleString()} unite="" couleur="#27AE60" icon="📈" />
              <KPICard titre="Capteurs actifs"     valeur={stats.length} unite="" couleur="#E67E22" icon="📡" />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
              <div style={{ background: "#fff", borderRadius: 12, padding: 20, boxShadow: "0 2px 12px rgba(0,0,0,0.08)" }}>
                <h3 style={{ margin: "0 0 16px", color: "#2C3E50", fontSize: 14 }}>🌡️ Température moyenne par quartier</h3>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={dataBarres}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
                    <XAxis dataKey="quartier" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
                    <YAxis domain={[24, 35]} tick={{ fontSize: 11 }} unit="°C" />
                    <Tooltip formatter={v => [`${v}°C`, "Température"]} />
                    <Bar dataKey="temperature" fill="#E05C5C" radius={[6,6,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div style={{ background: "#fff", borderRadius: 12, padding: 20, boxShadow: "0 2px 12px rgba(0,0,0,0.08)" }}>
                <h3 style={{ margin: "0 0 16px", color: "#2C3E50", fontSize: 14 }}>💧 Humidité moyenne par quartier</h3>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={dataBarres}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
                    <XAxis dataKey="quartier" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
                    <YAxis domain={[60, 100]} tick={{ fontSize: 11 }} unit="%" />
                    <Tooltip formatter={v => [`${v}%`, "Humidité"]} />
                    <Bar dataKey="humidite" fill="#2E86C1" radius={[6,6,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div style={{ background: "#fff", borderRadius: 12, padding: 20, boxShadow: "0 2px 12px rgba(0,0,0,0.08)", marginBottom: 20 }}>
              <h3 style={{ margin: "0 0 16px", color: "#2C3E50", fontSize: 14 }}>📈 Évolution température — temps réel</h3>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={dataCourbe}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
                  <XAxis dataKey="time" tick={{ fontSize: 10 }} />
                  <YAxis domain={[24, 36]} unit="°C" tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  {["Akwa","Bonanjo","Deido","Bepanda","Makepe"].map(q => (
                    <Line key={q} type="monotone" dataKey={q} stroke={COULEURS[q]} strokeWidth={2} dot={false} connectNulls />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div style={{ background: "#fff", borderRadius: 12, padding: 20, boxShadow: "0 2px 12px rgba(0,0,0,0.08)" }}>
              <h3 style={{ margin: "0 0 16px", color: "#2C3E50", fontSize: 14 }}>📊 Statistiques par capteur</h3>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ background: "#1A3A5C" }}>
                    {["Quartier","Mesures","Temp Min","Temp Moy","Temp Max","Hum Moy","Pres Moy"].map(h => (
                      <th key={h} style={{ color: "#fff", padding: "10px 14px", textAlign: "left", fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {stats.map((s, i) => (
                    <tr key={i} style={{ background: i % 2 === 0 ? "#F8FAFC" : "#fff" }}>
                      <td style={{ padding: "9px 14px", fontWeight: 600 }}>
                        <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: COULEURS[s.quartier] || "#ccc", marginRight: 8 }} />
                        {s.quartier}
                      </td>
                      <td style={{ padding: "9px 14px" }}>{s.nb_mesures?.toLocaleString()}</td>
                      <td style={{ padding: "9px 14px", color: "#2E86C1" }}>{s.temperature?.min?.toFixed(1)}°C</td>
                      <td style={{ padding: "9px 14px", fontWeight: 700, color: "#E05C5C" }}>{s.temperature?.moy?.toFixed(1)}°C</td>
                      <td style={{ padding: "9px 14px", color: "#E67E22" }}>{s.temperature?.max?.toFixed(1)}°C</td>
                      <td style={{ padding: "9px 14px" }}>{s.humidite?.moy?.toFixed(1)}%</td>
                      <td style={{ padding: "9px 14px" }}>{s.pression?.moy?.toFixed(1)} hPa</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {/* ── MESURES ── */}
        {activeTab === "mesures" && (
          <div style={{ background: "#fff", borderRadius: 12, padding: 24, boxShadow: "0 2px 12px rgba(0,0,0,0.08)" }}>
            <h3 style={{ margin: "0 0 16px", color: "#2C3E50" }}>📋 50 dernières mesures</h3>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ background: "#1A3A5C" }}>
                  {["Capteur","Quartier","Timestamp","Température","Humidité","Pression"].map(h => (
                    <th key={h} style={{ color: "#fff", padding: "10px 14px", textAlign: "left" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {mesures.map((m, i) => (
                  <tr key={i} style={{ background: i % 2 === 0 ? "#F8FAFC" : "#fff" }}>
                    <td style={{ padding: "8px 14px", fontFamily: "monospace", fontSize: 11 }}>{m.sensor_id}</td>
                    <td style={{ padding: "8px 14px" }}>
                      <span style={{ background: COULEURS[m.quartier] || "#ccc", color: "#fff", borderRadius: 12, padding: "2px 10px", fontSize: 11 }}>
                        {m.quartier}
                      </span>
                    </td>
                    <td style={{ padding: "8px 14px", color: "#7F8C8D", fontSize: 11 }}>{new Date(m.timestamp).toLocaleString()}</td>
                    <td style={{ padding: "8px 14px", fontWeight: 600, color: "#E05C5C" }}>{m.temperature}°C</td>
                    <td style={{ padding: "8px 14px", color: "#2E86C1" }}>{m.humidite}%</td>
                    <td style={{ padding: "8px 14px", color: "#27AE60" }}>{m.pression} hPa</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ── INSERTION ── */}
        {activeTab === "insertion" && <InsertionManuelle notifier={notifier} />}

        {/* ── CAPTEURS ── */}
        {activeTab === "capteurs" && <GestionCapteurs notifier={notifier} />}

        {/* ── CQL ── */}
        {activeTab === "cql" && <ConsoleCQL />}

      </div>
    </div>
  );
}