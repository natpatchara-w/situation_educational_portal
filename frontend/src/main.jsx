import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { BookOpen, Download, FileCheck2, FileText, LogOut, Search } from "lucide-react";
import "./styles.css";

const API_BASE = `http://${window.location.hostname}:8000`;
const CATEGORIES = [
  { value: "", label: "All files" },
  { value: "checklist", label: "Volunteer Checklists" },
  { value: "educational", label: "Educational Resources" },
];

function getCookie(name) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.method && options.method !== "GET" ? { "X-CSRFToken": getCookie("csrftoken") || "" } : {}),
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Something went wrong.");
  }

  return response.json();
}

function App() {
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [resources, setResources] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function bootstrap() {
      try {
        await apiFetch("/api/auth/csrf/");
        const currentUser = await apiFetch("/api/auth/me/");
        setUser(currentUser);
      } catch {
        setUser(null);
      } finally {
        setAuthChecked(true);
      }
    }

    bootstrap();
  }, []);

  useEffect(() => {
    if (!user) return;

    let active = true;
    async function loadResources() {
      setLoading(true);
      setError("");
      const params = new URLSearchParams();
      if (search.trim()) params.set("search", search.trim());
      if (category) params.set("category", category);

      try {
        const payload = await apiFetch(`/api/resources/?${params.toString()}`);
        if (!active) return;
        setResources(payload.resources);
      } catch (err) {
        if (active) setError(err.message);
      } finally {
        if (active) setLoading(false);
      }
    }

    const timer = window.setTimeout(loadResources, 250);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [user, search, category]);

  const resourceCounts = useMemo(
    () => ({
      checklist: resources.filter((item) => item.category === "checklist").length,
      educational: resources.filter((item) => item.category === "educational").length,
    }),
    [resources],
  );

  async function handleLogin(credentials) {
    await apiFetch("/api/auth/csrf/");
    const loggedInUser = await apiFetch("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
    setUser(loggedInUser);
  }

  async function handleLogout() {
    await apiFetch("/api/auth/logout/", { method: "POST" });
    setUser(null);
    setResources([]);
    setSearch("");
    setCategory("");
  }

  if (!authChecked) {
    return <StatusScreen message="Preparing your resource library..." />;
  }

  if (!user) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Student Volunteer Portal</p>
          <h1>Resource Library</h1>
        </div>
        <button className="ghost-button" onClick={handleLogout} type="button">
          <LogOut size={18} />
          Sign out
        </button>
      </header>

      <section className="summary-band" aria-label="Resource summary">
        <SummaryItem icon={<FileCheck2 />} label="Checklists" value={resourceCounts.checklist} />
        <SummaryItem icon={<BookOpen />} label="Educational resources" value={resourceCounts.educational} />
        <SummaryItem icon={<FileText />} label="Visible files" value={resources.length} />
      </section>

      <section className="controls" aria-label="Resource filters">
        <label className="search-field">
          <Search size={18} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by title or description"
          />
        </label>

        <div className="segmented-control" role="tablist" aria-label="Resource category">
          {CATEGORIES.map((item) => (
            <button
              key={item.value}
              className={category === item.value ? "active" : ""}
              onClick={() => setCategory(item.value)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </div>
      </section>

      {error && <p className="notice error">{error}</p>}
      {loading && <p className="notice">Loading resources...</p>}

      {!loading && resources.length === 0 ? (
        <section className="empty-state">
          <FileText size={36} />
          <h2>No files found</h2>
          <p>Try another search or ask a staff member to upload PDF or DOCX resources in Django admin.</p>
        </section>
      ) : (
        <section className="resource-grid" aria-label="Downloadable resources">
          {resources.map((resource) => (
            <ResourceCard key={resource.id} resource={resource} />
          ))}
        </section>
      )}
    </main>
  );
}

function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await onLogin({ username, password });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-panel">
        <p className="eyebrow">GMLS Volunteer Resources</p>
        <h1>Sign in to download resources</h1>
        <form onSubmit={submit}>
          <label>
            Username
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" />
          </label>
          <label>
            Password
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              autoComplete="current-password"
            />
          </label>
          {error && <p className="notice error">{error}</p>}
          <button className="primary-button" disabled={submitting} type="submit">
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}

function SummaryItem({ icon, label, value }) {
  return (
    <div className="summary-item">
      <span>{React.cloneElement(icon, { size: 22 })}</span>
      <div>
        <strong>{value}</strong>
        <p>{label}</p>
      </div>
    </div>
  );
}

function ResourceCard({ resource }) {
  const uploaded = new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(resource.uploadedAt));
  const downloadHref = `${API_BASE}${resource.downloadUrl}`;

  return (
    <article className="resource-card">
      <div className="card-header">
        <span className={`category-pill ${resource.category}`}>{resource.categoryLabel}</span>
        <span className="file-type">{resource.fileType}</span>
        <FileText size={22} />
      </div>
      <h2>{resource.title}</h2>
      <p>{resource.description || "No description provided."}</p>
      <div className="card-footer">
        <span>Uploaded {uploaded}</span>
        <a className="download-button" href={downloadHref}>
          <Download size={17} />
          Download
        </a>
      </div>
    </article>
  );
}

function StatusScreen({ message }) {
  return (
    <main className="status-screen">
      <p>{message}</p>
    </main>
  );
}

const rootElement = document.getElementById("root");
const root = globalThis.__volunteerPortalRoot || createRoot(rootElement);
globalThis.__volunteerPortalRoot = root;
root.render(<App />);
