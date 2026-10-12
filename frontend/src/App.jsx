
import { useState } from "react";
import {
  ShieldCheck,
  LayoutDashboard,
  Building2,
  Users,
  Smartphone,
  ShieldAlert,
  Search,
  Bell,
  Plus,
  Globe,
  Activity,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  Menu,
  X,
} from "lucide-react";
import "./App.css";

const initialFindings = [
  {
    id: 1,
    name: "Nova Fashion Support",
    type: "Social profile",
    target: "@nova_fashion_support",
    score: 82,
    status: "Needs review",
  },
  {
    id: 2,
    name: "Nova Shopping",
    type: "Mobile app",
    target: "Unknown publisher",
    score: 64,
    status: "Needs review",
  },
  {
    id: 3,
    name: "Royal Style Store",
    type: "Social profile",
    target: "@royal_style_store",
    score: 18,
    status: "Reviewed",
  },
];

const navigation = [
  { name: "Overview", icon: LayoutDashboard },
  { name: "Brand Profile", icon: Building2 },
  { name: "Social Monitoring", icon: Users },
  { name: "App Monitoring", icon: Smartphone },
  { name: "Findings", icon: ShieldAlert },
];

function App() {
  const [page, setPage] = useState("Overview");
  const [mobileNav, setMobileNav] = useState(false);
  const [brand, setBrand] = useState({
    name: "",
    website: "",
    social: "",
    publisher: "",
  });
  const [savedBrand, setSavedBrand] = useState(null);
  const [findings, setFindings] = useState(initialFindings);
  const [query, setQuery] = useState("");
  const [profile, setProfile] = useState({
    name: "",
    username: "",
    url: "",
  });
  const [appForm, setAppForm] = useState({
    name: "",
    publisher: "",
    url: "",
  });
  const [message, setMessage] = useState("");

  const reviewedCount = findings.filter(
    (item) => item.status === "Reviewed"
  ).length;

  function saveBrand(event) {
    event.preventDefault();
    setSavedBrand({ ...brand });
    setMessage("Brand profile saved successfully.");
  }

  function scanSocial(event) {
    event.preventDefault();
    if (!profile.name.trim()) return;

    const score = savedBrand
      ? Math.min(
          99,
          Math.round(
            (profile.name.toLowerCase().includes(
              savedBrand.name.toLowerCase()
            )
              ? 0.85
              : 0.4) * 100
          )
        )
      : 40;

    setFindings((old) => [
      {
        id: Date.now(),
        name: profile.name,
        type: "Social profile",
        target: profile.username || profile.url || "Manually submitted",
        score,
        status: "Needs review",
      },
      ...old,
    ]);

    setProfile({ name: "", username: "", url: "" });
    setMessage("Demo analysis completed. Review the risk score and evidence.");
  }

  function scanApp(event) {
    event.preventDefault();
    if (!appForm.name.trim()) return;

    const publisherMismatch =
      savedBrand?.publisher &&
      appForm.publisher.trim().toLowerCase() !==
        savedBrand.publisher.trim().toLowerCase();

    const score = publisherMismatch ? 78 : 42;

    setFindings((old) => [
      {
        id: Date.now(),
        name: appForm.name,
        type: "Mobile app",
        target: appForm.publisher || appForm.url || "Unknown publisher",
        score,
        status: "Needs review",
      },
      ...old,
    ]);

    setAppForm({ name: "", publisher: "", url: "" });
    setMessage("Demo app analysis completed. Please verify the result manually.");
  }

  function updateStatus(id) {
    setFindings((old) =>
      old.map((item) =>
        item.id === id
          ? {
              ...item,
              status:
                item.status === "Reviewed" ? "Needs review" : "Reviewed",
            }
          : item
      )
    );
  }

  const filteredFindings = findings.filter((item) =>
    `${item.name} ${item.type} ${item.target} ${item.status}`
      .toLowerCase()
      .includes(query.toLowerCase())
  );

  return (
    <div className="app-shell">
      {mobileNav && (
        <button
          className="mobile-overlay"
          aria-label="Close navigation"
          onClick={() => setMobileNav(false)}
        />
      )}

      <aside className={`sidebar ${mobileNav ? "sidebar-open" : ""}`}>
        <div className="brand-logo">
          <div className="logo-icon">
            <ShieldCheck size={24} />
          </div>
          <div>
            <h2>BrandShield<span> AI</span></h2>
            <p>DIGITAL RISK PROTECTION</p>
          </div>
          <button
            className="close-nav"
            onClick={() => setMobileNav(false)}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <div className="workspace-label">WORKSPACE</div>
        <nav className="navigation">
          {navigation.map(({ name, icon: Icon }) => (
            <button
              key={name}
              className={`nav-item ${page === name ? "active" : ""}`}
              onClick={() => {
                setPage(name);
                setMobileNav(false);
                setMessage("");
              }}
            >
              <Icon size={19} />
              <span>{name}</span>
              {name === "Findings" && (
                <span className="nav-count">{findings.length}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="protection-card">
            <div className="protection-icon">
              <Activity size={18} />
            </div>
            <h3>Protection status</h3>
            <p>Demo workspace active</p>
            <div className="status-line">
              <span />
              Ready for testing
            </div>
          </div>
          <div className="profile-mini">
            <div className="avatar">BS</div>
            <div>
              <strong>Security Analyst</strong>
              <p>Demo workspace</p>
            </div>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <button
            className="menu-toggle"
            onClick={() => setMobileNav(true)}
            aria-label="Open menu"
          >
            <Menu size={22} />
          </button>
          <div className="breadcrumb">
            Workspace <span>/</span> <strong>{page}</strong>
          </div>
          <div className="topbar-actions">
            <span className="environment"><span /> DEMO ENVIRONMENT</span>
            <button className="icon-button" aria-label="Notifications">
              <Bell size={19} />
            </button>
            <div className="top-avatar">BS</div>
          </div>
        </header>

        <div className="page-content">
          {message && (
            <div className="notice">
              <CheckCircle2 size={18} />
              <span>{message}</span>
              <button onClick={() => setMessage("")} aria-label="Dismiss">
                <X size={16} />
              </button>
            </div>
          )}

          {page === "Overview" && (
            <>
              <div className="welcome-row">
                <div>
                  <div className="eyebrow"><span /> SECURITY OVERVIEW</div>
                  <h1>Digital Risk Overview</h1>
                  <p className="page-subtitle">
                    Monitor brand exposure and investigate suspicious digital assets.
                  </p>
                </div>
                <button
                  className="primary-button"
                  onClick={() => setPage("Brand Profile")}
                >
                  <Plus size={18} /> Configure brand
                </button>
              </div>

              <div className="stats-grid">
                <StatCard
                  icon={ShieldAlert}
                  label="Total findings"
                  value={findings.length}
                  detail="Tracked in this demo"
                  tone="purple"
                />
                <StatCard
                  icon={Clock}
                  label="Needs review"
                  value={findings.filter((f) => f.status === "Needs review").length}
                  detail="Awaiting analyst review"
                  tone="orange"
                />
                <StatCard
                  icon={CheckCircle2}
                  label="Reviewed"
                  value={reviewedCount}
                  detail="Marked by the analyst"
                  tone="green"
                />
                <StatCard
                  icon={Activity}
                  label="High risk"
                  value={findings.filter((f) => f.score >= 75).length}
                  detail="Scores of 75 and above"
                  tone="blue"
                />
              </div>

              <section className="setup-banner">
                <div className="setup-icon"><ShieldCheck size={26} /></div>
                <div className="setup-copy">
                  <span className="section-kicker">GETTING STARTED</span>
                  <h2>{savedBrand ? "Your brand profile is configured" : "Set up your brand protection"}</h2>
                  <p>
                    {savedBrand
                      ? `Monitoring workspace for ${savedBrand.name}. Submit assets for demo analysis.`
                      : "Add your official brand details before testing suspicious social profiles and apps."}
                  </p>
                </div>
                <button
                  className="secondary-button"
                  onClick={() => setPage("Brand Profile")}
                >
                  {savedBrand ? "Edit profile" : "Set up profile"} <ArrowUpRight size={16} />
                </button>
              </section>

              <div className="section-heading">
                <div>
                  <h2>Recent findings</h2>
                  <p>Potential risks that may need investigation</p>
                </div>
                <button className="text-button" onClick={() => setPage("Findings")}>
                  View all findings <ArrowUpRight size={16} />
                </button>
              </div>

              <FindingsTable
                findings={findings.slice(0, 4)}
                onToggle={updateStatus}
              />

              <div className="section-heading quick-heading">
                <div>
                  <h2>Monitoring tools</h2>
                  <p>Submit assets for a local demonstration analysis</p>
                </div>
              </div>
              <div className="quick-grid">
                <QuickAction
                  icon={Users}
                  title="Social monitoring"
                  description="Check a submitted profile name and handle."
                  onClick={() => setPage("Social Monitoring")}
                />
                <QuickAction
                  icon={Smartphone}
                  title="App monitoring"
                  description="Review an app name and publisher."
                  onClick={() => setPage("App Monitoring")}
                />
                <QuickAction
                  icon={ShieldAlert}
                  title="Investigate findings"
                  description="Search, review, and update finding status."
                  onClick={() => setPage("Findings")}
                />
              </div>
            </>
          )}

          {page === "Brand Profile" && (
            <>
              <PageIntro
                eyebrow="BRAND CONFIGURATION"
                title="Brand Profile"
                subtitle="Define the official identity that your protection workflow should recognize."
              />
              <section className="panel form-panel">
                <div className="panel-title">
                  <div className="panel-icon"><Building2 size={20} /></div>
                  <div>
                    <h2>Official brand details</h2>
                    <p>Use accurate information for your demo tests.</p>
                  </div>
                </div>
                <form onSubmit={saveBrand} className="form-grid">
                  <label>
                    Brand or company name *
                    <input
                      required
                      value={brand.name}
                      onChange={(e) => setBrand({ ...brand, name: e.target.value })}
                      placeholder="e.g. Nova Fashion"
                    />
                  </label>
                  <label>
                    Official website
                    <input
                      type="url"
                      value={brand.website}
                      onChange={(e) => setBrand({ ...brand, website: e.target.value })}
                      placeholder="https://example.com"
                    />
                  </label>
                  <label>
                    Official social account
                    <input
                      value={brand.social}
                      onChange={(e) => setBrand({ ...brand, social: e.target.value })}
                      placeholder="@official_account"
                    />
                  </label>
                  <label>
                    Official app publisher
                    <input
                      value={brand.publisher}
                      onChange={(e) => setBrand({ ...brand, publisher: e.target.value })}
                      placeholder="Registered publisher name"
                    />
                  </label>
                  <div className="form-footer">
                    <p>* Required field</p>
                    <button type="submit" className="primary-button">
                      <CheckCircle2 size={17} /> Save brand profile
                    </button>
                  </div>
                </form>
              </section>

              <section className="panel saved-panel">
                <span className="section-kicker">CURRENT PROFILE</span>
                {savedBrand ? (
                  <div className="saved-brand">
                    <div className="saved-logo"><ShieldCheck size={25} /></div>
                    <div>
                      <h3>{savedBrand.name}</h3>
                      <p>{savedBrand.website || "No website added"}</p>
                      <p>{savedBrand.social || "No social account added"}</p>
                    </div>
                    <span className="pill green-pill">Saved in session</span>
                  </div>
                ) : (
                  <p className="empty-text">No brand profile saved yet. Complete the form above.</p>
                )}
              </section>
            </>
          )}

          {page === "Social Monitoring" && (
            <>
              <PageIntro
                eyebrow="SOCIAL MEDIA MONITORING"
                title="Social Monitoring"
                subtitle="Submit a suspicious social profile for an illustrative name-based risk check."
              />
              <div className="info-banner">
                <Globe size={20} />
                <p>This demo does not scan social platforms live. Enter a profile you want to evaluate.</p>
              </div>
              <section className="panel form-panel">
                <div className="panel-title">
                  <div className="panel-icon"><Users size={20} /></div>
                  <div>
                    <h2>Analyze a social profile</h2>
                    <p>Provide the name and any available account details.</p>
                  </div>
                </div>
                <form onSubmit={scanSocial} className="form-grid">
                  <label>
                    Profile or page name *
                    <input required value={profile.name} onChange={(e) => setProfile({ ...profile, name: e.target.value })} placeholder="e.g. Nova Fashion Support" />
                  </label>
                  <label>
                    Username or handle
                    <input value={profile.username} onChange={(e) => setProfile({ ...profile, username: e.target.value })} placeholder="@account_name" />
                  </label>
                  <label className="full-width">
                    Profile URL
                    <input type="url" value={profile.url} onChange={(e) => setProfile({ ...profile, url: e.target.value })} placeholder="https://social.example/profile" />
                  </label>
                  <div className="form-footer">
                    <p>Results are demo heuristics, not proof of impersonation.</p>
                    <button className="primary-button" type="submit"><Search size={17} /> Analyze profile</button>
                  </div>
                </form>
              </section>
              <div className="tip-card"><ShieldCheck size={20} /><p><strong>Analyst tip</strong> Compare account age, verified links, logo use, and official contact information before drawing conclusions.</p></div>
            </>
          )}

          {page === "App Monitoring" && (
            <>
              <PageIntro
                eyebrow="APPLICATION MONITORING"
                title="App Monitoring"
                subtitle="Review a submitted app listing for potential brand and publisher mismatches."
              />
              <div className="info-banner">
                <Smartphone size={20} />
                <p>This demo does not fetch live app store listings. Enter the app details to create a finding.</p>
              </div>
              <section className="panel form-panel">
                <div className="panel-title">
                  <div className="panel-icon"><Smartphone size={20} /></div>
                  <div>
                    <h2>Analyze an app listing</h2>
                    <p>Check the app name and developer or publisher information.</p>
                  </div>
                </div>
                <form onSubmit={scanApp} className="form-grid">
                  <label>
                    App name *
                    <input required value={appForm.name} onChange={(e) => setAppForm({ ...appForm, name: e.target.value })} placeholder="e.g. Nova Shopping" />
                  </label>
                  <label>
                    Developer or publisher
                    <input value={appForm.publisher} onChange={(e) => setAppForm({ ...appForm, publisher: e.target.value })} placeholder="Publisher shown in the store" />
                  </label>
                  <label className="full-width">
                    App store listing URL
                    <input type="url" value={appForm.url} onChange={(e) => setAppForm({ ...appForm, url: e.target.value })} placeholder="https://example.com/app" />
                  </label>
                  <div className="form-footer">
                    <p>Manually submitted app details only.</p>
                    <button className="primary-button" type="submit"><Search size={17} /> Analyze app</button>
                  </div>
                </form>
              </section>
              <div className="tip-card"><ShieldCheck size={20} /><p><strong>Analyst tip</strong> Verify the developer against the official publisher and check the app's permissions and privacy policy.</p></div>
            </>
          )}

          {page === "Findings" && (
            <>
              <PageIntro
                eyebrow="INVESTIGATION CENTER"
                title="Security Findings"
                subtitle="Search potential brand risks and record your review decisions."
              />
              <div className="finding-toolbar">
                <div className="search-box">
                  <Search size={18} />
                  <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search findings..." />
                </div>
                <span className="result-count">{filteredFindings.length} findings</span>
              </div>
              <FindingsTable findings={filteredFindings} onToggle={updateStatus} />
              <p className="disclaimer">Risk scores in this prototype are illustrative and must not be treated as verified fraud determinations.</p>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, detail, tone }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${tone}`}><Icon size={21} /></div>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-detail">{detail}</div>
    </div>
  );
}

function PageIntro({ eyebrow, title, subtitle }) {
  return (
    <div className="page-intro">
      <div className="eyebrow"><span /> {eyebrow}</div>
      <h1>{title}</h1>
      <p className="page-subtitle">{subtitle}</p>
    </div>
  );
}

function QuickAction({ icon: Icon, title, description, onClick }) {
  return (
    <button className="quick-card" onClick={onClick}>
      <div className="quick-icon"><Icon size={21} /></div>
      <div><h3>{title}</h3><p>{description}</p></div>
      <ArrowUpRight className="quick-arrow" size={18} />
    </button>
  );
}

function FindingsTable({ findings, onToggle }) {
  return (
    <div className="panel table-panel">
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>ASSET / ENTITY</th>
              <th>TYPE</th>
              <th>IDENTIFIER</th>
              <th>RISK SCORE</th>
              <th>STATUS</th>
              <th>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {findings.map((item) => (
              <tr key={item.id}>
                <td><div className="entity-name">{item.name}</div><div className="entity-sub">Potential brand exposure</div></td>
                <td>{item.type}</td>
                <td className="identifier">{item.target}</td>
                <td><div className="score-cell"><strong>{item.score}</strong><div className="score-track"><span style={{ width: `${item.score}%` }} /></div></div></td>
                <td><span className={`pill ${item.status === "Reviewed" ? "green-pill" : "orange-pill"}`}>{item.status}</span></td>
                <td><button className="review-button" onClick={() => onToggle(item.id)}>{item.status === "Reviewed" ? "Reopen" : "Review"}</button></td>
              </tr>
            ))}
            {findings.length === 0 && (
              <tr><td colSpan="6" className="empty-row">No findings match your search.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default App;
