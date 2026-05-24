import { useState, useEffect, useRef } from "react";

// ── Mock data to simulate live tender fetches ────────────────────────────────
const MOCK_TENDERS = [
  {
    id: "T001", title: "Development of AI-Based Disease Surveillance System",
    organization: "Ministry of Health & Family Welfare", portal: "CPPP (eProcure)",
    govt_type: "Central", state: null, deadline: "2025-06-15",
    value: "₹4.2 Crore", published: "2025-05-22",
    keywords: ["AI", "Machine Learning", "Data Analytics"],
    url: "https://eprocure.gov.in", status: "new",
    summary: "Development of an AI-powered epidemiological surveillance dashboard integrating real-time data from district hospitals. Requires ML models for outbreak prediction and a mobile-responsive web platform.",
    opportunity: "AI/ML", urgency: "Medium", scope: "Large"
  },
  {
    id: "T002", title: "Smart City Command & Control Centre Software Platform",
    organization: "Pune Smart City Development Corporation",
    portal: "Smart Cities Mission", govt_type: "State", state: "Maharashtra",
    deadline: "2025-06-08", value: "₹12.5 Crore", published: "2025-05-22",
    keywords: ["Smart City", "IoT", "Cloud", "Data Analytics"],
    url: "https://smartcities.gov.in", status: "new",
    summary: "Integrated software platform for Pune Smart City Centre. Covers traffic management, CCTV analytics, citizen services, and IoT sensor data aggregation on cloud infrastructure.",
    opportunity: "Digital Infrastructure", urgency: "High", scope: "Large"
  },
  {
    id: "T003", title: "Cloud Migration of Legacy ERP Systems",
    organization: "Food Corporation of India",
    portal: "GeM Portal", govt_type: "Central", state: null,
    deadline: "2025-06-20", value: "₹2.8 Crore", published: "2025-05-22",
    keywords: ["Cloud", "ERP", "Software Development"],
    url: "https://bidplus.gem.gov.in", status: "new",
    summary: "Migration of FCI's legacy Oracle ERP to cloud-native architecture (AWS/Azure). Includes data migration, integration testing, staff training, and 3-year managed support.",
    opportunity: "Cloud", urgency: "Medium", scope: "Large"
  },
  {
    id: "T004", title: "Cybersecurity Audit and VAPT Services",
    organization: "State Bank of India (IT Dept)",
    portal: "NIC Tenders", govt_type: "Central", state: null,
    deadline: "2025-05-30", value: "₹85 Lakh", published: "2025-05-22",
    keywords: ["Cybersecurity", "VAPT", "IT Security"],
    url: "https://www.nic.in/tenders", status: "new",
    summary: "Comprehensive vulnerability assessment and penetration testing for SBI's internet banking, mobile app, and 200+ branch servers. CERT-In empanelled agency required.",
    opportunity: "Cybersecurity", urgency: "High", scope: "Medium"
  },
  {
    id: "T005", title: "AI-Powered Crop Advisory Mobile Application",
    organization: "Karnataka Dept of Agriculture",
    portal: "Karnataka eProcurement", govt_type: "State", state: "Karnataka",
    deadline: "2025-06-28", value: "₹1.2 Crore", published: "2025-05-22",
    keywords: ["AI", "Mobile App", "Deep Learning", "IoT"],
    url: "https://eproc.karnataka.gov.in", status: "new",
    summary: "Native Android/iOS app using computer vision for crop disease detection from photos. Includes Kannada language support, SMS fallback, and integration with weather APIs.",
    opportunity: "AI/ML", urgency: "Low", scope: "Medium"
  },
  {
    id: "T006", title: "Data Centre Establishment and IT Infrastructure",
    organization: "Rajasthan State Data Centre",
    portal: "Rajasthan eProcurement", govt_type: "State", state: "Rajasthan",
    deadline: "2025-07-10", value: "₹28 Crore", published: "2025-05-21",
    keywords: ["IT Infrastructure", "Cloud", "Cybersecurity", "Networking"],
    url: "https://sppp.rajasthan.gov.in", status: "reported",
    summary: "Tier-III data centre with 200 rack units, 99.982% uptime SLA. Includes storage, networking, security appliances, and 5-year AMC. Must comply with MeitY guidelines.",
    opportunity: "IT Services", urgency: "Low", scope: "Large"
  },
  {
    id: "T007", title: "Embedded Software for Smart Meter Reading System",
    organization: "BESCOM (Karnataka Power Utility)",
    portal: "Karnataka eProcurement", govt_type: "State", state: "Karnataka",
    deadline: "2025-06-03", value: "₹3.6 Crore", published: "2025-05-21",
    keywords: ["Embedded Systems", "IoT", "Electronics", "Firmware"],
    url: "https://eproc.karnataka.gov.in", status: "reported",
    summary: "Firmware development for 50,000 smart electricity meters with NB-IoT connectivity, tamper detection, and remote load control. DLMS/COSEM protocol compliance mandatory.",
    opportunity: "Electronics", urgency: "High", scope: "Large"
  },
  {
    id: "T008", title: "Machine Learning Platform for Tax Fraud Detection",
    organization: "Income Tax Department, CBDT",
    portal: "CPPP (eProcure)", govt_type: "Central", state: null,
    deadline: "2025-06-30", value: "Not disclosed", published: "2025-05-22",
    keywords: ["Machine Learning", "Data Science", "AI", "Big Data"],
    url: "https://eprocure.gov.in", status: "new",
    summary: "ML-based anomaly detection platform for identifying tax evasion patterns across 8 crore ITR filings. Requires explainable AI components for legal compliance. On-premises deployment.",
    opportunity: "Data Science", urgency: "Low", scope: "Unknown"
  },
];

const STATS = {
  total: 127, today: 8, central: 47, state: 80,
  portals: 14, ai_ml: 23, software: 31, cloud: 19,
  cyber: 12, electronics: 15, other: 27
};

// ── Color helpers ─────────────────────────────────────────────────────────────
const OPPORTUNITY_COLORS = {
  "AI/ML": { bg: "#fef3c7", text: "#92400e", dot: "#f59e0b" },
  "Software Dev": { bg: "#dbeafe", text: "#1e40af", dot: "#3b82f6" },
  "IT Services": { bg: "#f0fdf4", text: "#166534", dot: "#22c55e" },
  "Electronics": { bg: "#fdf4ff", text: "#6b21a8", dot: "#a855f7" },
  "Cybersecurity": { bg: "#fff1f2", text: "#881337", dot: "#f43f5e" },
  "Cloud": { bg: "#ecfeff", text: "#155e75", dot: "#06b6d4" },
  "Data Science": { bg: "#fffbeb", text: "#78350f", dot: "#f97316" },
  "Automation": { bg: "#f0f9ff", text: "#0c4a6e", dot: "#0ea5e9" },
  "Digital Infrastructure": { bg: "#f5f3ff", text: "#3730a3", dot: "#6366f1" },
  "Other": { bg: "#f9fafb", text: "#374151", dot: "#6b7280" },
};

const URGENCY_STYLES = {
  "High (< 7 days)": { bg: "#fee2e2", text: "#991b1b" },
  "High": { bg: "#fee2e2", text: "#991b1b" },
  "Medium": { bg: "#fef3c7", text: "#92400e" },
  "Medium (7-30 days)": { bg: "#fef3c7", text: "#92400e" },
  "Low": { bg: "#dcfce7", text: "#166534" },
  "Low (> 30 days)": { bg: "#dcfce7", text: "#166534" },
};

// ── Pulsing dot ───────────────────────────────────────────────────────────────
function LiveDot() {
  return (
    <span style={{ position: "relative", display: "inline-flex", marginRight: 8 }}>
      <span style={{
        width: 10, height: 10, borderRadius: "50%", background: "#22c55e",
        display: "inline-block", animation: "ping 1.5s ease-in-out infinite",
        position: "absolute", opacity: 0.6
      }} />
      <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#22c55e", display: "inline-block" }} />
    </span>
  );
}

// ── Stat card ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, sub, accent }) {
  return (
    <div style={{
      background: "white", borderRadius: 12, padding: "18px 20px",
      border: "1px solid #e2e8f0", position: "relative", overflow: "hidden"
    }}>
      <div style={{
        position: "absolute", top: 0, left: 0, width: 4, height: "100%",
        background: accent || "#2563eb", borderRadius: "12px 0 0 12px"
      }} />
      <div style={{ fontSize: 28, fontWeight: 800, color: "#0f172a", letterSpacing: "-1px" }}>{value}</div>
      <div style={{ fontSize: 13, fontWeight: 600, color: "#64748b", marginTop: 2 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

// ── Tender row ────────────────────────────────────────────────────────────────
function TenderRow({ tender, onSelect, selected }) {
  const opp = OPPORTUNITY_COLORS[tender.opportunity] || OPPORTUNITY_COLORS["Other"];
  const urg = URGENCY_STYLES[tender.urgency] || URGENCY_STYLES["Low"];
  const isNew = tender.status === "new";

  return (
    <div
      onClick={() => onSelect(tender)}
      style={{
        padding: "14px 20px", borderBottom: "1px solid #f1f5f9",
        cursor: "pointer", transition: "background 0.15s",
        background: selected ? "#eff6ff" : (isNew ? "white" : "#fafafa"),
        borderLeft: isNew ? "3px solid #22c55e" : "3px solid transparent",
      }}
      onMouseEnter={e => e.currentTarget.style.background = selected ? "#eff6ff" : "#f8fafc"}
      onMouseLeave={e => e.currentTarget.style.background = selected ? "#eff6ff" : (isNew ? "white" : "#fafafa")}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 4 }}>
            {isNew && (
              <span style={{ fontSize: 10, fontWeight: 700, background: "#dcfce7", color: "#166534",
                padding: "1px 6px", borderRadius: 10, letterSpacing: "0.5px" }}>NEW</span>
            )}
            <span style={{ fontSize: 11, background: opp.bg, color: opp.text,
              padding: "2px 8px", borderRadius: 10, fontWeight: 600 }}>
              {tender.opportunity}
            </span>
            <span style={{ fontSize: 11, background: tender.govt_type === "Central" ? "#dbeafe" : "#f3e8ff",
              color: tender.govt_type === "Central" ? "#1d4ed8" : "#7e22ce",
              padding: "2px 8px", borderRadius: 10, fontWeight: 600 }}>
              {tender.state || "Central"}
            </span>
          </div>
          <div style={{ fontWeight: 700, fontSize: 14, color: "#0f172a", lineHeight: 1.4, marginBottom: 4 }}>
            {tender.title}
          </div>
          <div style={{ fontSize: 12, color: "#64748b" }}>
            {tender.organization} · <span style={{ color: "#94a3b8" }}>{tender.portal}</span>
          </div>
        </div>
        <div style={{ textAlign: "right", flexShrink: 0, minWidth: 110 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#059669", marginBottom: 4 }}>
            {tender.value}
          </div>
          <div style={{ fontSize: 11, ...urg, padding: "2px 8px", borderRadius: 8, fontWeight: 600 }}>
            Due: {tender.deadline}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Detail panel ──────────────────────────────────────────────────────────────
function DetailPanel({ tender, onClose }) {
  if (!tender) return (
    <div style={{
      display: "flex", flexDirection: "column", alignItems: "center",
      justifyContent: "center", height: "100%", color: "#94a3b8", padding: 40
    }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
      <div style={{ fontSize: 15, fontWeight: 600 }}>Select a tender to view details</div>
    </div>
  );

  const opp = OPPORTUNITY_COLORS[tender.opportunity] || OPPORTUNITY_COLORS["Other"];

  return (
    <div style={{ padding: 24, height: "100%", overflowY: "auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 20 }}>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: "#64748b", textTransform: "uppercase" }}>
          Tender Details
        </span>
        <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer",
          fontSize: 18, color: "#94a3b8", lineHeight: 1 }}>✕</button>
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
        <span style={{ ...opp, padding: "4px 12px", borderRadius: 20, fontSize: 12, fontWeight: 700 }}>
          {tender.opportunity}
        </span>
        {tender.govt_type === "Central"
          ? <span style={{ background: "#dbeafe", color: "#1d4ed8", padding: "4px 12px", borderRadius: 20, fontSize: 12, fontWeight: 700 }}>Central Govt</span>
          : <span style={{ background: "#f3e8ff", color: "#7e22ce", padding: "4px 12px", borderRadius: 20, fontSize: 12, fontWeight: 700 }}>State · {tender.state}</span>
        }
      </div>

      <h2 style={{ fontSize: 17, fontWeight: 800, color: "#0f172a", margin: "0 0 16px 0", lineHeight: 1.4 }}>
        {tender.title}
      </h2>

      <div style={{ background: "#f8fafc", borderRadius: 10, padding: 16, marginBottom: 20 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: "#64748b", marginBottom: 8, letterSpacing: 0.5 }}>
          AI SUMMARY
        </div>
        <p style={{ margin: 0, fontSize: 13, color: "#334155", lineHeight: 1.6 }}>{tender.summary}</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Organization", value: tender.organization },
          { label: "Portal Source", value: tender.portal },
          { label: "Published", value: tender.published },
          { label: "Deadline", value: tender.deadline },
          { label: "Tender Value", value: tender.value },
          { label: "Scope", value: tender.scope },
        ].map(({ label, value }) => (
          <div key={label} style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 8, padding: 12 }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: "#94a3b8", letterSpacing: 0.5, textTransform: "uppercase" }}>{label}</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#0f172a", marginTop: 4 }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", letterSpacing: 0.5, marginBottom: 8 }}>
          MATCHED KEYWORDS
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {tender.keywords.map(k => (
            <span key={k} style={{ background: "#f1f5f9", color: "#475569",
              padding: "3px 10px", borderRadius: 8, fontSize: 12, fontWeight: 500 }}>{k}</span>
          ))}
        </div>
      </div>

      <a
        href={tender.url}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          display: "block", textAlign: "center", background: "#1e3a5f",
          color: "white", padding: "12px 20px", borderRadius: 10, textDecoration: "none",
          fontWeight: 700, fontSize: 14, letterSpacing: 0.3
        }}
      >
        🔗 View Official Tender Portal
      </a>
    </div>
  );
}

// ── Live AI Fetch Simulator ────────────────────────────────────────────────────
function AIFetchSimulator({ onComplete }) {
  const [step, setStep] = useState(0);
  const [logs, setLogs] = useState([]);

  const STEPS = [
    "🌐 Connecting to CPPP (eProcure)...",
    "✓ CPPP: Fetched 43 raw tenders",
    "🌐 Connecting to GeM Portal...",
    "✓ GeM: Fetched 67 bid listings",
    "🌐 Scanning 10 state portals...",
    "✓ Karnataka: 12 | Tamil Nadu: 9 | Maharashtra: 14",
    "🌐 Scanning NIC, PSUs, Smart Cities...",
    "✓ MeitY: 4 | CDAC: 3 | DRDO: 2",
    "⚙️  Running keyword filter (80+ keywords)...",
    "✓ 37 relevant tenders identified",
    "🤖 Claude AI summarizing tenders...",
    "✓ AI summaries generated",
    "💾 Deduplication check against database...",
    "✓ 8 new tenders (29 already reported)",
    "📧 Sending email report...",
    "✓ Report delivered to 3 recipients",
    "✅ Cycle complete — 8 new tech tenders found!"
  ];

  useEffect(() => {
    if (step < STEPS.length) {
      const delay = step === 0 ? 300 : (STEPS[step - 1].startsWith("✓") ? 400 : 900);
      const timer = setTimeout(() => {
        setLogs(prev => [...prev, { text: STEPS[step], isCheck: STEPS[step].startsWith("✓") }]);
        setStep(s => s + 1);
      }, delay);
      return () => clearTimeout(timer);
    } else {
      setTimeout(onComplete, 800);
    }
  }, [step]);

  return (
    <div style={{
      background: "#0d1117", borderRadius: 12, padding: 24,
      fontFamily: "'Fira Code', 'Courier New', monospace", fontSize: 13
    }}>
      <div style={{ color: "#58a6ff", marginBottom: 16, fontWeight: 700 }}>
        $ python main.py --mode run-once
      </div>
      {logs.map((log, i) => (
        <div key={i} style={{
          color: log.isCheck ? "#3fb950" : "#c9d1d9",
          marginBottom: 6, opacity: i === logs.length - 1 ? 1 : 0.8
        }}>
          {log.text}
        </div>
      ))}
      {step < STEPS.length && (
        <div style={{ color: "#58a6ff", marginTop: 6 }}>
          <span style={{ animation: "blink 1s infinite" }}>█</span>
        </div>
      )}
    </div>
  );
}

// ── Architecture diagram ───────────────────────────────────────────────────────
function ArchDiagram() {
  const nodes = [
    { x: 50, y: 10, w: 200, label: "SCHEDULER", sub: "APScheduler • 10AM + 7PM IST", color: "#1e3a5f" },
    { x: 50, y: 80, w: 200, label: "SCRAPER ENGINE", sub: "CPPP · GeM · 10 States · NIC/PSUs", color: "#2563eb" },
    { x: 50, y: 150, w: 200, label: "PROCESSOR PIPELINE", sub: "Keyword Filter → Claude AI Summarizer", color: "#7c3aed" },
    { x: 50, y: 220, w: 200, label: "DATABASE", sub: "SQLite / PostgreSQL • Deduplication", color: "#059669" },
    { x: 50, y: 290, w: 200, label: "REPORTERS", sub: "Email HTML · Google Sheets", color: "#d97706" },
  ];

  return (
    <svg viewBox="0 0 300 370" style={{ width: "100%", maxWidth: 300 }}>
      <defs>
        <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L0,6 L8,3 z" fill="#94a3b8" />
        </marker>
      </defs>
      {nodes.map((n, i) => (
        <g key={i}>
          <rect x={n.x} y={n.y} width={n.w} height={52} rx={8}
            fill={n.color} opacity={0.95} />
          <text x={n.x + n.w / 2} y={n.y + 20} textAnchor="middle"
            fill="white" fontSize={11} fontWeight="700" fontFamily="sans-serif">
            {n.label}
          </text>
          <text x={n.x + n.w / 2} y={n.y + 36} textAnchor="middle"
            fill="rgba(255,255,255,0.75)" fontSize={9} fontFamily="sans-serif">
            {n.sub}
          </text>
          {i < nodes.length - 1 && (
            <line x1={150} y1={n.y + 52} x2={150} y2={n.y + 66}
              stroke="#94a3b8" strokeWidth={1.5} markerEnd="url(#arr)" />
          )}
        </g>
      ))}
    </svg>
  );
}

// ── Main Dashboard ─────────────────────────────────────────────────────────────
export default function TenderMonitorDashboard() {
  const [tab, setTab] = useState("dashboard");
  const [selectedTender, setSelectedTender] = useState(null);
  const [filter, setFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showSimulator, setShowSimulator] = useState(false);
  const [simDone, setSimDone] = useState(false);
  const [currentTime, setCurrentTime] = useState("");

  // IST clock
  useEffect(() => {
    const tick = () => {
      const ist = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata",
        hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: true });
      setCurrentTime(ist);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const filteredTenders = MOCK_TENDERS.filter(t => {
    const matchFilter = filter === "all" || filter === t.govt_type.toLowerCase()
      || filter === t.opportunity.toLowerCase().replace(/\//g, "").replace(/ /g, "");
    const matchSearch = !searchQuery || t.title.toLowerCase().includes(searchQuery.toLowerCase())
      || t.organization.toLowerCase().includes(searchQuery.toLowerCase())
      || t.keywords.some(k => k.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchFilter && matchSearch;
  });

  const tabs = [
    { id: "dashboard", label: "📊 Dashboard" },
    { id: "tenders", label: "📋 Live Tenders" },
    { id: "simulator", label: "⚡ Run Demo" },
    { id: "architecture", label: "🏗️ Architecture" },
    { id: "setup", label: "🚀 Setup Guide" },
  ];

  return (
    <div style={{
      minHeight: "100vh", background: "#f1f5f9",
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
    }}>
      <style>{`
        @keyframes ping { 0%,100%{transform:scale(1);opacity:0.6} 50%{transform:scale(2);opacity:0} }
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
        @keyframes slideIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 6px; } 
        ::-webkit-scrollbar-track { background: #f1f5f9; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
      `}</style>

      {/* Header */}
      <div style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e3a5f 60%, #1e40af 100%)",
        padding: "20px 32px", color: "white"
      }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                <LiveDot />
                <span style={{ fontSize: 11, color: "#86efac", fontWeight: 600, letterSpacing: 1 }}>
                  LIVE · IST {currentTime}
                </span>
              </div>
              <h1 style={{ margin: 0, fontSize: 22, fontWeight: 900, letterSpacing: "-0.5px" }}>
                🔍 AI Tender Monitor
              </h1>
              <p style={{ margin: "4px 0 0", fontSize: 13, color: "#93c5fd" }}>
                Indian Government Tech Tenders — Automated · AI-Powered · Daily
              </p>
            </div>
            <div style={{ textAlign: "right", opacity: 0.85 }}>
              <div style={{ fontSize: 12, color: "#bfdbfe" }}>Next scan</div>
              <div style={{ fontSize: 15, fontWeight: 700 }}>Today · 7:00 PM IST</div>
              <div style={{ fontSize: 11, color: "#93c5fd", marginTop: 2 }}>14 portals monitored</div>
            </div>
          </div>

          {/* Tabs */}
          <div style={{ display: "flex", gap: 4, marginTop: 20, borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: 0 }}>
            {tabs.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)} style={{
                background: tab === t.id ? "rgba(255,255,255,0.15)" : "transparent",
                border: "none", color: tab === t.id ? "white" : "rgba(255,255,255,0.6)",
                padding: "8px 16px", borderRadius: "8px 8px 0 0", cursor: "pointer",
                fontSize: 13, fontWeight: tab === t.id ? 700 : 500,
                borderBottom: tab === t.id ? "2px solid #60a5fa" : "2px solid transparent",
                transition: "all 0.15s"
              }}>
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: "0 auto", padding: 24 }}>

        {/* ── DASHBOARD TAB ─────────────────────────────────────────────────── */}
        {tab === "dashboard" && (
          <div style={{ animation: "slideIn 0.3s ease" }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 16, marginBottom: 28 }}>
              <StatCard label="Total Tenders Tracked" value={STATS.total} sub="All time" accent="#2563eb" />
              <StatCard label="Found Today" value={STATS.today} sub="May 22, 2025" accent="#22c55e" />
              <StatCard label="Central Govt" value={STATS.central} sub="CPPP, GeM, NIC..." accent="#7c3aed" />
              <StatCard label="State Portals" value={STATS.state} sub="10 states active" accent="#d97706" />
              <StatCard label="AI/ML Tenders" value={STATS.ai_ml} sub="High priority" accent="#f43f5e" />
              <StatCard label="Portals Monitored" value={STATS.portals} sub="Daily scraping" accent="#06b6d4" />
            </div>

            {/* Category breakdown */}
            <div style={{ background: "white", borderRadius: 12, padding: 24, border: "1px solid #e2e8f0", marginBottom: 24 }}>
              <h3 style={{ margin: "0 0 20px 0", fontSize: 15, fontWeight: 800, color: "#0f172a" }}>
                Tenders by Technology Category
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {[
                  { label: "Software Development", count: 31, max: 50, color: "#3b82f6" },
                  { label: "AI / Machine Learning", count: 23, max: 50, color: "#f59e0b" },
                  { label: "Cloud Computing", count: 19, max: 50, color: "#06b6d4" },
                  { label: "Electronics & Embedded", count: 15, max: 50, color: "#a855f7" },
                  { label: "Cybersecurity", count: 12, max: 50, color: "#f43f5e" },
                  { label: "Data Science", count: 10, max: 50, color: "#f97316" },
                  { label: "Automation & IoT", count: 8, max: 50, color: "#22c55e" },
                  { label: "Other IT Services", count: 9, max: 50, color: "#64748b" },
                ].map(item => (
                  <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div style={{ width: 160, fontSize: 13, color: "#374151", fontWeight: 500, flexShrink: 0 }}>
                      {item.label}
                    </div>
                    <div style={{ flex: 1, height: 8, background: "#f1f5f9", borderRadius: 4, overflow: "hidden" }}>
                      <div style={{
                        width: `${(item.count / item.max) * 100}%`, height: "100%",
                        background: item.color, borderRadius: 4,
                        transition: "width 1s ease"
                      }} />
                    </div>
                    <div style={{ width: 30, textAlign: "right", fontSize: 13, fontWeight: 700, color: "#0f172a" }}>
                      {item.count}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top today */}
            <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", overflow: "hidden" }}>
              <div style={{ padding: "16px 20px", borderBottom: "1px solid #f1f5f9", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3 style={{ margin: 0, fontSize: 15, fontWeight: 800, color: "#0f172a" }}>
                  Today's Top Tenders
                </h3>
                <button onClick={() => setTab("tenders")} style={{
                  background: "#eff6ff", color: "#2563eb", border: "none",
                  padding: "6px 14px", borderRadius: 8, cursor: "pointer", fontSize: 12, fontWeight: 600
                }}>
                  View All →
                </button>
              </div>
              {MOCK_TENDERS.filter(t => t.status === "new").slice(0, 4).map(t => (
                <TenderRow key={t.id} tender={t}
                  onSelect={() => { setSelectedTender(t); setTab("tenders"); }}
                  selected={false} />
              ))}
            </div>
          </div>
        )}

        {/* ── TENDERS TAB ───────────────────────────────────────────────────── */}
        {tab === "tenders" && (
          <div style={{ animation: "slideIn 0.3s ease", display: "grid", gridTemplateColumns: "1fr 380px", gap: 20 }}>
            <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", overflow: "hidden" }}>
              {/* Search + filter bar */}
              <div style={{ padding: "16px 20px", borderBottom: "1px solid #f1f5f9", display: "flex", gap: 12, flexWrap: "wrap" }}>
                <input
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  placeholder="🔍 Search tenders, orgs, keywords..."
                  style={{
                    flex: 1, minWidth: 200, padding: "8px 14px", borderRadius: 8,
                    border: "1px solid #e2e8f0", fontSize: 13, outline: "none",
                    fontFamily: "inherit"
                  }}
                />
                <select
                  value={filter}
                  onChange={e => setFilter(e.target.value)}
                  style={{
                    padding: "8px 14px", borderRadius: 8, border: "1px solid #e2e8f0",
                    fontSize: 13, fontFamily: "inherit", background: "white", cursor: "pointer"
                  }}
                >
                  <option value="all">All Types</option>
                  <option value="central">Central Govt</option>
                  <option value="state">State Govt</option>
                  <option value="AI/ML">AI / ML</option>
                  <option value="Cloud">Cloud</option>
                  <option value="Cybersecurity">Cybersecurity</option>
                </select>
              </div>

              <div style={{ fontSize: 12, color: "#64748b", padding: "10px 20px", background: "#f8fafc",
                borderBottom: "1px solid #f1f5f9", fontWeight: 600 }}>
                {filteredTenders.length} tenders found
                {searchQuery && ` matching "${searchQuery}"`}
              </div>

              <div style={{ maxHeight: 580, overflowY: "auto" }}>
                {filteredTenders.length === 0
                  ? <div style={{ padding: 40, textAlign: "center", color: "#94a3b8" }}>No tenders match your filter</div>
                  : filteredTenders.map(t => (
                    <TenderRow key={t.id} tender={t}
                      onSelect={setSelectedTender}
                      selected={selectedTender?.id === t.id} />
                  ))
                }
              </div>
            </div>

            <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", overflow: "hidden" }}>
              <DetailPanel tender={selectedTender} onClose={() => setSelectedTender(null)} />
            </div>
          </div>
        )}

        {/* ── SIMULATOR TAB ─────────────────────────────────────────────────── */}
        {tab === "simulator" && (
          <div style={{ animation: "slideIn 0.3s ease", maxWidth: 700, margin: "0 auto" }}>
            <div style={{ background: "white", borderRadius: 12, padding: 24, border: "1px solid #e2e8f0", marginBottom: 20 }}>
              <h2 style={{ margin: "0 0 8px 0", fontSize: 18, fontWeight: 800, color: "#0f172a" }}>
                ⚡ Live Fetch Simulation
              </h2>
              <p style={{ margin: "0 0 20px 0", fontSize: 14, color: "#64748b" }}>
                Watch the system fetch tenders from all portals, run AI filtering, 
                summarize with Claude, and deliver the report.
              </p>
              {!showSimulator && (
                <button
                  onClick={() => { setShowSimulator(true); setSimDone(false); }}
                  style={{
                    background: "linear-gradient(135deg, #1e3a5f, #2563eb)",
                    color: "white", border: "none", padding: "12px 28px",
                    borderRadius: 10, cursor: "pointer", fontWeight: 700,
                    fontSize: 15, letterSpacing: 0.3, width: "100%"
                  }}
                >
                  🚀 Start Demo Run
                </button>
              )}
            </div>

            {showSimulator && (
              <div style={{ animation: "slideIn 0.3s ease" }}>
                <AIFetchSimulator onComplete={() => setSimDone(true)} />
                {simDone && (
                  <div style={{
                    background: "white", borderRadius: 12, padding: 24,
                    border: "1px solid #e2e8f0", marginTop: 16,
                    animation: "slideIn 0.4s ease"
                  }}>
                    <h3 style={{ margin: "0 0 16px 0", fontSize: 15, fontWeight: 800, color: "#059669" }}>
                      ✅ Report Ready — 8 New Tech Tenders
                    </h3>
                    <p style={{ margin: "0 0 16px 0", color: "#64748b", fontSize: 13 }}>
                      Email delivered to 3 recipients · Google Sheet updated
                    </p>
                    <button
                      onClick={() => setTab("tenders")}
                      style={{
                        background: "#eff6ff", color: "#2563eb", border: "1px solid #bfdbfe",
                        padding: "10px 20px", borderRadius: 8, cursor: "pointer",
                        fontWeight: 700, fontSize: 13, marginRight: 12
                      }}
                    >
                      View Tenders →
                    </button>
                    <button
                      onClick={() => { setShowSimulator(false); setSimDone(false); }}
                      style={{
                        background: "#f8fafc", color: "#374151", border: "1px solid #e2e8f0",
                        padding: "10px 20px", borderRadius: 8, cursor: "pointer",
                        fontWeight: 600, fontSize: 13
                      }}
                    >
                      Run Again
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ── ARCHITECTURE TAB ──────────────────────────────────────────────── */}
        {tab === "architecture" && (
          <div style={{ animation: "slideIn 0.3s ease", display: "grid", gridTemplateColumns: "300px 1fr", gap: 24 }}>
            <div style={{ background: "white", borderRadius: 12, padding: 24, border: "1px solid #e2e8f0" }}>
              <h3 style={{ margin: "0 0 20px 0", fontSize: 15, fontWeight: 800, color: "#0f172a" }}>System Flow</h3>
              <ArchDiagram />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {[
                { title: "14 Government Portals Monitored", color: "#2563eb", items: ["CPPP (Central Public Procurement)", "GeM (Govt e-Marketplace)", "10 State eProcurement portals", "NIC, MeitY, CDAC, STPI", "Railways (IREPS), PSUs", "Smart Cities Mission"] },
                { title: "80+ Technology Keywords", color: "#7c3aed", items: ["AI, Machine Learning, Deep Learning", "Software, Web, Mobile App, ERP", "Cloud, DevOps, SaaS, PaaS", "IoT, Electronics, Embedded", "Cybersecurity, VAPT, SIEM", "Data Science, Analytics, BI"] },
                { title: "Automation Features", color: "#059669", items: ["Runs 10:00 AM & 7:00 PM IST daily", "Automatic retry on portal failure", "Duplicate detection across all cycles", "AI summaries via Claude Haiku", "Email HTML report + Google Sheets", "SQLite / PostgreSQL storage"] },
              ].map(section => (
                <div key={section.title} style={{ background: "white", borderRadius: 12, padding: 20, border: "1px solid #e2e8f0" }}>
                  <h3 style={{ margin: "0 0 14px 0", fontSize: 14, fontWeight: 800, color: "#0f172a" }}>
                    <span style={{ color: section.color }}>●</span> {section.title}
                  </h3>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {section.items.map(item => (
                      <div key={item} style={{ display: "flex", gap: 8, fontSize: 13, color: "#475569" }}>
                        <span style={{ color: section.color, flexShrink: 0 }}>→</span> {item}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── SETUP TAB ─────────────────────────────────────────────────────── */}
        {tab === "setup" && (
          <div style={{ animation: "slideIn 0.3s ease", maxWidth: 800, margin: "0 auto" }}>
            {[
              {
                step: "1", title: "Install Dependencies",
                color: "#2563eb",
                code: `git clone <your-repo> && cd tender_monitor
pip install -r requirements.txt`
              },
              {
                step: "2", title: "Configure .env File",
                color: "#7c3aed",
                code: `cp .env.example .env

# Edit .env with your values:
ANTHROPIC_API_KEY=sk-ant-your-key-here
EMAIL_ENABLED=true
EMAIL_SENDER=youremail@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
EMAIL_RECIPIENTS=you@email.com,team@company.com`
              },
              {
                step: "3", title: "Test Run (Single Cycle)",
                color: "#059669",
                code: `python main.py --mode run-once
# Output: Fetching → Filtering → Summarizing → Reporting`
              },
              {
                step: "4", title: "Start Daily Automation",
                color: "#d97706",
                code: `# Option A: Direct (stays in terminal)
python main.py --mode scheduler

# Option B: Docker (recommended for VPS)
docker-compose up -d
docker logs -f tender_monitor

# Option C: systemd service (Linux VPS)
sudo systemctl start tender_monitor`
              },
              {
                step: "5", title: "Add More Portals",
                color: "#f43f5e",
                code: `# In scrapers/state_scraper.py → STATE_PORTALS list:
{
    "name": "New State eProcurement",
    "state": "New State",
    "url": "https://tender.newstate.gov.in",
    "tender_list_path": "/tenders",
    "row_selector": "table tr",
    "cols": {"title": 0, "org": 1, "pub_date": 2, "deadline": 3},
},`
              },
            ].map(({ step, title, color, code }) => (
              <div key={step} style={{ background: "white", borderRadius: 12, padding: 24, border: "1px solid #e2e8f0", marginBottom: 16 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16 }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: "50%", background: color,
                    color: "white", fontWeight: 900, fontSize: 16,
                    display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0
                  }}>{step}</div>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 800, color: "#0f172a" }}>{title}</h3>
                </div>
                <pre style={{
                  background: "#0d1117", color: "#c9d1d9", padding: 20,
                  borderRadius: 10, fontSize: 12, overflowX: "auto",
                  margin: 0, lineHeight: 1.7, fontFamily: "'Fira Code', monospace"
                }}>
                  {code}
                </pre>
              </div>
            ))}

            <div style={{ background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 12, padding: 20 }}>
              <h3 style={{ margin: "0 0 10px 0", fontSize: 14, fontWeight: 800, color: "#92400e" }}>
                📌 Important: Gmail App Password
              </h3>
              <p style={{ margin: 0, fontSize: 13, color: "#78350f", lineHeight: 1.6 }}>
                You need a Gmail App Password (not your regular password):<br />
                1. Enable 2-Step Verification on your Google Account<br />
                2. Go to: Google Account → Security → App Passwords<br />
                3. Generate a 16-character password → paste into EMAIL_PASSWORD
              </p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
