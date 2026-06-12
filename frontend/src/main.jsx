import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BookOpen,
  Download,
  Eye,
  FileCheck2,
  FilePlus2,
  FileText,
  Library,
  LoaderCircle,
  LogOut,
  Search,
  Upload,
  WandSparkles,
} from "lucide-react";
import "./styles.css";

const API_BASE = getApiBase();
const CATEGORIES = [
  { value: "", label: "All files" },
  { value: "checklist", label: "Volunteer Checklists" },
  { value: "educational", label: "Educational Resources" },
];

function getApiBase() {
  const configuredBase =
    import.meta.env.VITE_API_BASE || window.__VOLUNTEER_API_BASE__ || `http://${window.location.hostname}:8000`;
  return configuredBase.replace(/\/$/, "");
}

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
  const [activePage, setActivePage] = useState("library");
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
    setActivePage("library");
  }

  function selectGeneratorPage() {
    if (user.canGenerateChecklist) setActivePage("generator");
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
          <h1>{activePage === "library" ? "Resource Library" : "Generate Checklist"}</h1>
        </div>
        <button className="ghost-button" onClick={handleLogout} type="button">
          <LogOut size={18} />
          Sign out
        </button>
      </header>

      <nav className="page-tabs" aria-label="Portal pages">
        <button className={activePage === "library" ? "active" : ""} onClick={() => setActivePage("library")} type="button">
          <Library size={18} />
          Resource Library
        </button>
        {user.canGenerateChecklist && (
          <button className={activePage === "generator" ? "active" : ""} onClick={selectGeneratorPage} type="button">
            <WandSparkles size={18} />
            Generate Checklist
          </button>
        )}
      </nav>

      {activePage === "generator" && user.canGenerateChecklist ? (
        <ChecklistGenerator />
      ) : (
        <ResourceLibrary
          category={category}
          error={error}
          loading={loading}
          resourceCounts={resourceCounts}
          resources={resources}
          search={search}
          setCategory={setCategory}
          setSearch={setSearch}
        />
      )}
    </main>
  );
}

function ResourceLibrary({ category, error, loading, resourceCounts, resources, search, setCategory, setSearch }) {
  return (
    <>
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
    </>
  );
}

function ChecklistGenerator() {
  const [queue, setQueue] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [processingId, setProcessingId] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [previewUrls, setPreviewUrls] = useState({});
  const [previewLoadingId, setPreviewLoadingId] = useState("");
  const [previewError, setPreviewError] = useState({ id: "", message: "" });
  const previewUrlsRef = useRef({});
  const previewRequestsRef = useRef(new Set());

  useEffect(() => {
    let active = true;
    async function loadJobs() {
      try {
        const payload = await apiFetch("/api/checklists/jobs/");
        if (!active) return;
        const jobs = payload.jobs.map(normalizeJob);
        setQueue(jobs);
        setSelectedId((current) => current || jobs[0]?.id || null);
      } catch (err) {
        if (active) setLoadError(err.message);
      }
    }

    loadJobs();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    return () => {
      Object.values(previewUrlsRef.current).forEach((url) => window.URL.revokeObjectURL(url));
    };
  }, []);

  useEffect(() => {
    if (processingId) return;

    const nextItem = queue.find((item) => item.status === "pending");
    if (!nextItem) return;

    setProcessingId(nextItem.id);
    setQueue((items) =>
      items.map((item) => (item.id === nextItem.id ? { ...item, status: "processing", error: "" } : item)),
    );

    createQueueJob(nextItem)
      .then((job) => {
        const normalizedJob = normalizeJob(job);
        setQueue((items) =>
          items.map((item) => (item.id === nextItem.id ? normalizedJob : item)),
        );
        setSelectedId((current) => (current === nextItem.id || !current ? normalizedJob.id : current));
      })
      .catch((err) => {
        setQueue((items) =>
          items.map((item) => (item.id === nextItem.id ? { ...item, status: "error", error: err.message } : item)),
        );
        setSelectedId((current) => current || nextItem.id);
      })
      .finally(() => {
        setProcessingId(null);
      });
  }, [processingId, queue]);

  const selectedItem = queue.find((item) => item.id === selectedId) || queue[0];
  const pendingCount = queue.filter((item) => item.status === "pending").length;
  const processingCount = queue.filter((item) => item.status === "processing").length;
  const doneCount = queue.filter((item) => item.status === "done").length;

  useEffect(() => {
    if (!selectedItem || selectedItem.status !== "done" || !selectedItem.previewUrl) return;
    if (previewUrls[selectedItem.id] || previewRequestsRef.current.has(selectedItem.id)) return;

    let active = true;
    previewRequestsRef.current.add(selectedItem.id);
    setPreviewLoadingId(selectedItem.id);
    setPreviewError({ id: "", message: "" });

    fetchPdfBlobUrl(selectedItem.previewUrl)
      .then((url) => {
        if (!active) {
          window.URL.revokeObjectURL(url);
          return;
        }
        previewUrlsRef.current = { ...previewUrlsRef.current, [selectedItem.id]: url };
        setPreviewUrls((current) => ({ ...current, [selectedItem.id]: url }));
      })
      .catch((err) => {
        if (active) setPreviewError({ id: selectedItem.id, message: err.message });
      })
      .finally(() => {
        previewRequestsRef.current.delete(selectedItem.id);
        if (active) setPreviewLoadingId("");
      });

    return () => {
      active = false;
    };
  }, [previewUrls, selectedItem]);

  function addFiles(fileList) {
    const files = Array.from(fileList || []).filter((item) => item.name.toLowerCase().endsWith(".docx"));
    if (files.length === 0) return;

    const newItems = files.map((item) => ({
      id: `${Date.now()}-${item.name}-${Math.random().toString(16).slice(2)}`,
      file: item,
      inputFilename: item.name,
      status: "pending",
      error: "",
      outputFilename: "volunteer-checklist.pdf",
      previewUrl: "",
      downloadUrl: "",
    }));

    setQueue((items) => [...newItems, ...items]);
    setSelectedId(newItems[0].id);
  }

  async function downloadSelected() {
    if (!selectedItem?.downloadUrl) return;
    try {
      const url = await fetchPdfBlobUrl(selectedItem.downloadUrl);
      downloadUrl(url, selectedItem.outputFilename);
      window.setTimeout(() => window.URL.revokeObjectURL(url), 1000);
    } catch (err) {
      setPreviewError({ id: selectedItem.id, message: err.message });
    }
  }

  return (
    <section className="generator-workspace" aria-label="Generate checklist PDF">
      <div className="generator-panel">
        <div>
          <p className="eyebrow">AI Checklist Generator</p>
          <h2>Upload Event Concept Notes</h2>
          <p>
            Add one or more DOCX files. Each concept note is processed in order and saved in the queue for preview
            before download.
          </p>
        </div>

        <div className="upload-form">
          {loadError && <p className="notice error">{loadError}</p>}
          <label className="upload-dropzone">
            <Upload size={26} />
            <span>Add DOCX files to queue</span>
            <input
              accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              multiple
              onChange={(event) => {
                addFiles(event.target.files);
                event.target.value = "";
              }}
              type="file"
            />
          </label>

          <div className="queue-stats" aria-label="Queue status">
            <SummaryItem icon={<LoaderCircle />} label="Processing" value={processingCount} />
            <SummaryItem icon={<FileText />} label="Waiting" value={pendingCount} />
            <SummaryItem icon={<FileCheck2 />} label="Ready" value={doneCount} />
          </div>
        </div>
      </div>

      <div className="queue-layout">
        <aside className="queue-list" aria-label="Checklist generation queue">
          <div className="queue-list-header">
            <FilePlus2 size={19} />
            <h2>Processing Queue</h2>
          </div>

          {queue.length === 0 ? (
            <p className="queue-empty">No documents in the queue.</p>
          ) : (
            queue.map((item) => (
              <button
                className={`queue-item ${selectedItem?.id === item.id ? "active" : ""}`}
                key={item.id}
                onClick={() => setSelectedId(item.id)}
                type="button"
              >
                <span className={`status-dot ${item.status}`} />
                <span>
                  <strong>{item.inputFilename}</strong>
                  <small>{getQueueStatusLabel(item)}</small>
                  {item.expiresAt && <small>Expires {formatQueueTime(item.expiresAt)}</small>}
                </span>
              </button>
            ))
          )}
        </aside>

        <section className="preview-panel" aria-label="Checklist preview">
          {!selectedItem ? (
            <div className="preview-empty">
              <Eye size={32} />
              <h2>Preview will appear here</h2>
              <p>Add DOCX files to generate volunteer checklist PDFs.</p>
            </div>
          ) : selectedItem.status === "done" ? (
            <>
              <div className="preview-header">
                <div>
                  <p className="eyebrow">PDF Preview</p>
                  <h2>{selectedItem.outputFilename}</h2>
                </div>
                <button className="download-button" onClick={downloadSelected} type="button">
                  <Download size={17} />
                  Download
                </button>
              </div>
              {previewError.id === selectedItem.id ? (
                <div className="preview-empty">
                  <FileText size={32} />
                  <h2>Preview unavailable</h2>
                  <p>{previewError.message}</p>
                </div>
              ) : previewUrls[selectedItem.id] ? (
                <iframe className="pdf-preview" src={previewUrls[selectedItem.id]} title={selectedItem.outputFilename} />
              ) : (
                <div className="preview-empty">
                  <LoaderCircle className="spin" size={32} />
                  <h2>Loading preview</h2>
                  <p>Preparing the generated PDF preview.</p>
                </div>
              )}
            </>
          ) : (
            <div className="preview-empty">
              {selectedItem.status === "error" ? <FileText size={32} /> : <LoaderCircle className="spin" size={32} />}
              <h2>{selectedItem.inputFilename}</h2>
              <p>{selectedItem.status === "error" ? selectedItem.error : getQueueStatusLabel(selectedItem)}</p>
            </div>
          )}
        </section>
      </div>
    </section>
  );
}

async function createQueueJob(item) {
  const formData = new FormData();
  formData.append("concept_note", item.file);

  await apiFetch("/api/auth/csrf/");
  const response = await fetch(`${API_BASE}/api/checklists/jobs/create/`, {
    method: "POST",
    credentials: "include",
    headers: {
      "X-CSRFToken": getCookie("csrftoken") || "",
    },
    body: formData,
  });

  const payload = await response.json().catch(() => ({}));
  if (payload.job) return payload.job;
  if (!response.ok) throw new Error(payload.detail || "Checklist generation failed.");
  throw new Error("Checklist generation returned an invalid response.");
}

async function fetchPdfBlobUrl(path) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Could not load the generated PDF.");
  }

  const blob = await response.blob();
  return window.URL.createObjectURL(blob);
}

function getQueueStatusLabel(item) {
  if (item.status === "pending") return "Waiting to process";
  if (item.status === "processing") return "Generating checklist";
  if (item.status === "done") return "Ready to preview";
  return item.error || "Generation failed";
}

function downloadUrl(url, filename) {
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
}

function normalizeJob(job) {
  return {
    id: String(job.id),
    inputFilename: job.inputFilename,
    outputFilename: job.outputFilename || "volunteer-checklist.pdf",
    status: job.status,
    error: job.error || "",
    previewUrl: job.previewUrl || "",
    downloadUrl: job.downloadUrl || "",
    expiresAt: job.expiresAt,
  };
}

function formatQueueTime(value) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
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
