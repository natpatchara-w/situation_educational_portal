import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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
  MessageCircle,
  Plus,
  Search,
  Send,
  Settings,
  Trash2,
  Upload,
  WandSparkles,
} from "lucide-react";
import "./styles.css";

const configuredApiBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || window.__VOLUNTEER_API_BASE__ || "";
const API_BASE = (
  configuredApiBase || (import.meta.env.DEV ? `http://${window.location.hostname}:8000` : window.location.origin)
).replace(/\/$/, "");

const ORGANIZATION_LOGOS = [
  { src: "/brand/logo-umn-emblem.png", alt: "UMN Universitas Multimedia Nusantara" },
  { src: "/brand/logo-gmls.png", alt: "Gugus Mitigasi Lebak Selatan" },
];
const LANGUAGE_STORAGE_KEY = "volunteerPortalLanguage";
let csrfToken = "";
let authToken = window.localStorage.getItem("volunteerAuthToken") || "";
const LANGUAGES = [
  { value: "en", shortLabel: "EN", labelKey: "languageEnglish" },
  { value: "id", shortLabel: "ID", labelKey: "languageIndonesian" },
];
const CATEGORIES = [
  { value: "", labelKey: "categoryAll" },
  { value: "checklist", labelKey: "categoryChecklist" },
  { value: "educational", labelKey: "categoryEducational" },
];
const PAGE_TITLES = {
  library: "pageLibrary",
  chat: "pageChat",
  generator: "pageGenerator",
  settings: "pageSettings",
};

const TRANSLATIONS = {
  en: {
    active: "Active",
    addDocxFiles: "Add DOCX files to queue",
    addWebsite: "Add Website",
    addWebsiteSource: "Add Website Source",
    aiAcknowledgement: "I understand uploaded concept notes will be sent to OpenAI for checklist generation.",
    aiChecklistGenerator: "AI Checklist Generator",
    answerSources: "Answer sources",
    appEyebrow: "Student Volunteer Portal",
    categoryAll: "All files",
    categoryChecklist: "Volunteer Checklists",
    categoryEducational: "Educational Resources",
    chatAria: "Education resource chat",
    chatPlaceholder: "Ask about safety, preparedness, evacuation, or volunteer learning materials",
    chatSourcesEyebrow: "Education Chat Sources",
    chatWelcome: "Ask a question about the portal education resources.",
    checklists: "Checklists",
    confirmAiBeforeFiles: "Confirm AI processing before adding files.",
    configuredWebsiteSources: "Configured website sources",
    download: "Download",
    downloadableResources: "Downloadable resources",
    educationResources: "Educational resources",
    emptyGenerator: "Add DOCX files to generate volunteer checklist PDFs.",
    errorGenerationFailed: "Generation failed",
    expires: "Expires {time}",
    fileNoDescription: "No description provided.",
    fileUploaded: "Uploaded {date}",
    generatorAria: "Generate checklist PDF",
    generatorDescription:
      "Add one or more DOCX files. Each concept note is processed in order and saved in the queue for preview before download.",
    gmlsEducationPage: "GMLS education page",
    loginEyebrow: "GMLS Volunteer Resources",
    inactive: "Inactive",
    label: "Label",
    languageEnglish: "English",
    languageIndonesian: "Indonesian",
    languageToggleLabel: "Language",
    loadingPreview: "Loading preview",
    loadingResources: "Loading resources...",
    noFilesFound: "No files found",
    noFilesHelp: "Try another search or ask a staff member to upload PDF or DOCX resources in Django admin.",
    noQueuedDocuments: "No documents in the queue.",
    noWebsiteSources: "No website sources added.",
    pageChat: "Education Chat",
    pageGenerator: "Generate Checklist",
    pageLibrary: "Resource Library",
    pageSettings: "Settings",
    password: "Password",
    pdfPreview: "PDF Preview",
    portalPages: "Portal pages",
    preparingLibrary: "Preparing your resource library...",
    preparingPreview: "Preparing the generated PDF preview.",
    previewAria: "Checklist preview",
    previewUnavailable: "Preview unavailable",
    previewWillAppear: "Preview will appear here",
    processing: "Processing",
    processingQueue: "Processing Queue",
    queueAria: "Checklist generation queue",
    queueStatus: "Queue status",
    ready: "Ready",
    resourceFilters: "Resource filters",
    resourceSummary: "Resource summary",
    searchPlaceholder: "Search by title or description",
    send: "Send",
    searchingEducation: "Searching education resources...",
    reasoning: "reasoning",
    settingsAria: "Education chat settings",
    signIn: "Sign in",
    signInHeading: "Sign in to download resources",
    signInLoading: "Signing in...",
    signOut: "Sign out",
    sourceActive: "Active",
    sourceInactive: "Inactive",
    statusDone: "Ready to preview",
    statusPending: "Waiting to process",
    statusProcessing: "Generating checklist",
    uploadedLanguage: "Language: {language}",
    uploadConceptNotes: "Upload Event Concept Notes",
    username: "Username",
    visibleFiles: "Visible files",
    waiting: "Waiting",
    websiteSources: "Website Sources",
    websiteUrl: "Website URL",
  },
  id: {
    active: "Aktif",
    addDocxFiles: "Tambahkan file DOCX ke antrean",
    addWebsite: "Tambahkan Situs",
    addWebsiteSource: "Tambahkan Sumber Situs",
    aiAcknowledgement: "Saya memahami catatan konsep yang diunggah akan dikirim ke OpenAI untuk membuat daftar periksa.",
    aiChecklistGenerator: "Pembuat Daftar Periksa AI",
    answerSources: "Sumber jawaban",
    appEyebrow: "Portal Relawan Mahasiswa",
    categoryAll: "Semua file",
    categoryChecklist: "Daftar Periksa Relawan",
    categoryEducational: "Materi Edukasi",
    chatAria: "Chat materi edukasi",
    chatPlaceholder: "Tanyakan tentang keselamatan, kesiapsiagaan, evakuasi, atau materi belajar relawan",
    chatSourcesEyebrow: "Sumber Chat Edukasi",
    chatWelcome: "Ajukan pertanyaan tentang materi edukasi portal.",
    checklists: "Daftar periksa",
    confirmAiBeforeFiles: "Konfirmasi pemrosesan AI sebelum menambahkan file.",
    configuredWebsiteSources: "Sumber situs yang dikonfigurasi",
    download: "Unduh",
    downloadableResources: "Materi yang dapat diunduh",
    educationResources: "Materi edukasi",
    emptyGenerator: "Tambahkan file DOCX untuk membuat PDF daftar periksa relawan.",
    errorGenerationFailed: "Pembuatan gagal",
    expires: "Berakhir {time}",
    fileNoDescription: "Tidak ada deskripsi.",
    fileUploaded: "Diunggah {date}",
    generatorAria: "Buat PDF daftar periksa",
    generatorDescription:
      "Tambahkan satu atau beberapa file DOCX. Setiap catatan konsep diproses berurutan dan disimpan di antrean untuk pratinjau sebelum diunduh.",
    gmlsEducationPage: "Halaman edukasi GMLS",
    loginEyebrow: "Materi Relawan GMLS",
    inactive: "Tidak aktif",
    label: "Label",
    languageEnglish: "Inggris",
    languageIndonesian: "Indonesia",
    languageToggleLabel: "Bahasa",
    loadingPreview: "Memuat pratinjau",
    loadingResources: "Memuat materi...",
    noFilesFound: "Tidak ada file ditemukan",
    noFilesHelp: "Coba pencarian lain atau minta staf mengunggah materi PDF atau DOCX di Django admin.",
    noQueuedDocuments: "Tidak ada dokumen dalam antrean.",
    noWebsiteSources: "Belum ada sumber situs.",
    pageChat: "Chat Edukasi",
    pageGenerator: "Buat Daftar Periksa",
    pageLibrary: "Perpustakaan Materi",
    pageSettings: "Pengaturan",
    password: "Kata sandi",
    pdfPreview: "Pratinjau PDF",
    portalPages: "Halaman portal",
    preparingLibrary: "Menyiapkan perpustakaan materi...",
    preparingPreview: "Menyiapkan pratinjau PDF yang dibuat.",
    previewAria: "Pratinjau daftar periksa",
    previewUnavailable: "Pratinjau tidak tersedia",
    previewWillAppear: "Pratinjau akan muncul di sini",
    processing: "Diproses",
    processingQueue: "Antrean Pemrosesan",
    queueAria: "Antrean pembuatan daftar periksa",
    queueStatus: "Status antrean",
    ready: "Siap",
    resourceFilters: "Filter materi",
    resourceSummary: "Ringkasan materi",
    searchPlaceholder: "Cari berdasarkan judul atau deskripsi",
    send: "Kirim",
    searchingEducation: "Mencari materi edukasi...",
    reasoning: "penalaran",
    settingsAria: "Pengaturan chat edukasi",
    signIn: "Masuk",
    signInHeading: "Masuk untuk mengunduh materi",
    signInLoading: "Sedang masuk...",
    signOut: "Keluar",
    sourceActive: "Aktif",
    sourceInactive: "Tidak aktif",
    statusDone: "Siap dipratinjau",
    statusPending: "Menunggu diproses",
    statusProcessing: "Membuat daftar periksa",
    uploadedLanguage: "Bahasa: {language}",
    uploadConceptNotes: "Unggah Catatan Konsep Kegiatan",
    username: "Nama pengguna",
    visibleFiles: "File terlihat",
    waiting: "Menunggu",
    websiteSources: "Sumber Situs",
    websiteUrl: "URL Situs",
  },
};

const API_ERROR_TRANSLATIONS = {
  id: {
    "AI checklist generation is disabled.": "Pembuatan daftar periksa AI sedang dinonaktifkan.",
    "AI processing acknowledgement is required.": "Persetujuan pemrosesan AI wajib diberikan.",
    "Authentication required.": "Autentikasi diperlukan.",
    "Chat message is too long.": "Pesan chat terlalu panjang.",
    "Checklist generation failed.": "Pembuatan daftar periksa gagal.",
    "Checklist generation failed. Please try again.": "Pembuatan daftar periksa gagal. Silakan coba lagi.",
    "Checklist generation limit reached. Try again later.": "Batas pembuatan daftar periksa tercapai. Coba lagi nanti.",
    "Checklist generation permission required.": "Izin membuat daftar periksa diperlukan.",
    "Checklist generation returned an invalid response.": "Pembuatan daftar periksa mengembalikan respons tidak valid.",
    "Checklist PDF is not ready.": "PDF daftar periksa belum siap.",
    "Could not load the generated PDF.": "Tidak dapat memuat PDF yang dibuat.",
    "Enter a public http or https website URL.": "Masukkan URL situs publik http atau https.",
    "Enter a question for the education chat.": "Masukkan pertanyaan untuk chat edukasi.",
    "GPT returned an empty answer. Please try again.": "GPT mengembalikan jawaban kosong. Silakan coba lagi.",
    "Invalid JSON payload.": "Payload JSON tidak valid.",
    "Invalid username or password.": "Nama pengguna atau kata sandi tidak valid.",
    "OpenAI API key is not configured. Ask an admin to add it in Django admin.":
      "Kunci API OpenAI belum dikonfigurasi. Minta admin menambahkannya di Django admin.",
    "OpenAI API key is not configured. Ask an admin to add it in settings.":
      "Kunci API OpenAI belum dikonfigurasi. Minta admin menambahkannya di pengaturan.",
    "Search is too long.": "Pencarian terlalu panjang.",
    "Something went wrong.": "Terjadi kesalahan.",
    "Staff permission required.": "Izin staf diperlukan.",
    "The DOCX file does not contain readable text.": "File DOCX tidak berisi teks yang dapat dibaca.",
    "This website is already in chat settings.": "Situs ini sudah ada di pengaturan chat.",
    "Too many login attempts. Try again later.": "Terlalu banyak percobaan masuk. Coba lagi nanti.",
    "Unsupported language.": "Bahasa tidak didukung.",
    "Upload a DOCX Event Concept Note.": "Unggah Catatan Konsep Kegiatan dalam format DOCX.",
    "Upload a readable DOCX Event Concept Note.": "Unggah Catatan Konsep Kegiatan DOCX yang dapat dibaca.",
    "Website removed.": "Situs dihapus.",
    "Website source not found.": "Sumber situs tidak ditemukan.",
  },
};

function getCookie(name) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

function getCsrfToken() {
  return csrfToken || getCookie("csrftoken") || "";
}

function rememberCsrfToken(payload) {
  if (payload?.csrfToken) csrfToken = payload.csrfToken;
}

function rememberAuthToken(payload) {
  if (!payload?.authToken) return;
  authToken = payload.authToken;
  window.localStorage.setItem("volunteerAuthToken", authToken);
}

function forgetAuthToken() {
  authToken = "";
  window.localStorage.removeItem("volunteerAuthToken");
}

function getAuthHeaders() {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {};
}

function getInitialLanguage() {
  if (typeof window === "undefined") return "en";
  const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  return LANGUAGES.some((item) => item.value === stored) ? stored : "en";
}

function translate(key, language, replacements = {}) {
  const text = TRANSLATIONS[language]?.[key] || TRANSLATIONS.en[key] || key;
  return text.replace(/\{(\w+)\}/g, (_match, name) => replacements[name] ?? "");
}

function translateApiError(message, language) {
  return API_ERROR_TRANSLATIONS[language]?.[message] || message;
}

function localeForLanguage(language) {
  return language === "id" ? "id-ID" : "en";
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...(options.method && options.method !== "GET" ? { "X-CSRFToken": getCsrfToken() } : {}),
      ...options.headers,
    },
    ...options,
  });

  const payload = await response.json().catch(() => ({}));
  rememberCsrfToken(payload);
  rememberAuthToken(payload);

  if (!response.ok) {
    if (response.status === 401) forgetAuthToken();
    throw new Error(payload.detail || "Something went wrong.");
  }

  return payload;
}

function App() {
  const [language, setLanguage] = useState(getInitialLanguage);
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [activePage, setActivePage] = useState("library");
  const [resources, setResources] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const t = useMemo(() => (key, replacements) => translate(key, language, replacements), [language]);

  useEffect(() => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    document.documentElement.lang = language;
  }, [language]);

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
        if (active) setError(translateApiError(err.message, language));
      } finally {
        if (active) setLoading(false);
      }
    }

    const timer = window.setTimeout(loadResources, 250);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [user, search, category, language]);

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
    await apiFetch("/api/auth/logout/", { method: "POST" }).catch(() => {});
    forgetAuthToken();
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
    return <StatusScreen message={t("preparingLibrary")} />;
  }

  if (!user) {
    return <LoginScreen language={language} onLanguageChange={setLanguage} onLogin={handleLogin} t={t} />;
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-heading">
          <BrandMarks compact />
          <div>
            <p className="eyebrow">{t("appEyebrow")}</p>
            <h1>{t(PAGE_TITLES[activePage] || PAGE_TITLES.library)}</h1>
          </div>
        </div>
        <div className="topbar-actions">
          <LanguageToggle language={language} onChange={setLanguage} t={t} />
          <button className="ghost-button" onClick={handleLogout} type="button">
            <LogOut size={18} />
            {t("signOut")}
          </button>
        </div>
      </header>

      <nav className="page-tabs" aria-label={t("portalPages")}>
        <button className={activePage === "library" ? "active" : ""} onClick={() => setActivePage("library")} type="button">
          <Library size={18} />
          {t("pageLibrary")}
        </button>
        <button className={activePage === "chat" ? "active" : ""} onClick={() => setActivePage("chat")} type="button">
          <MessageCircle size={18} />
          {t("pageChat")}
        </button>
        {user.canGenerateChecklist && (
          <button className={activePage === "generator" ? "active" : ""} onClick={selectGeneratorPage} type="button">
            <WandSparkles size={18} />
            {t("pageGenerator")}
          </button>
        )}
        {user.isStaff && (
          <button className={activePage === "settings" ? "active" : ""} onClick={() => setActivePage("settings")} type="button">
            <Settings size={18} />
            {t("pageSettings")}
          </button>
        )}
      </nav>

      {activePage === "chat" ? (
        <EducationChat language={language} t={t} />
      ) : activePage === "settings" && user.isStaff ? (
        <SettingsPage language={language} t={t} />
      ) : activePage === "generator" && user.canGenerateChecklist ? (
        <ChecklistGenerator language={language} t={t} />
      ) : (
        <ResourceLibrary
          category={category}
          error={error}
          language={language}
          loading={loading}
          resourceCounts={resourceCounts}
          resources={resources}
          search={search}
          setCategory={setCategory}
          setSearch={setSearch}
          t={t}
        />
      )}
    </main>
  );
}

function LanguageToggle({ language, onChange, t }) {
  return (
    <div className="segmented-control language-toggle" role="group" aria-label={t("languageToggleLabel")}>
      {LANGUAGES.map((item) => (
        <button
          key={item.value}
          className={language === item.value ? "active" : ""}
          onClick={() => onChange(item.value)}
          title={t(item.labelKey)}
          type="button"
        >
          {item.shortLabel}
        </button>
      ))}
    </div>
  );
}

function ResourceLibrary({
  category,
  error,
  language,
  loading,
  resourceCounts,
  resources,
  search,
  setCategory,
  setSearch,
  t,
}) {
  return (
    <>
      <section className="summary-band" aria-label={t("resourceSummary")}>
        <SummaryItem icon={<FileCheck2 />} label={t("checklists")} value={resourceCounts.checklist} />
        <SummaryItem icon={<BookOpen />} label={t("educationResources")} value={resourceCounts.educational} />
        <SummaryItem icon={<FileText />} label={t("visibleFiles")} value={resources.length} />
      </section>

      <section className="controls" aria-label={t("resourceFilters")}>
        <label className="search-field">
          <Search size={18} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={t("searchPlaceholder")}
          />
        </label>

        <div className="segmented-control" role="tablist" aria-label={t("resourceFilters")}>
          {CATEGORIES.map((item) => (
            <button
              key={item.value}
              className={category === item.value ? "active" : ""}
              onClick={() => setCategory(item.value)}
              type="button"
            >
              {t(item.labelKey)}
            </button>
          ))}
        </div>
      </section>

      {error && <p className="notice error">{error}</p>}
      {loading && <p className="notice">{t("loadingResources")}</p>}

      {!loading && resources.length === 0 ? (
        <section className="empty-state">
          <FileText size={36} />
          <h2>{t("noFilesFound")}</h2>
          <p>{t("noFilesHelp")}</p>
        </section>
      ) : (
        <section className="resource-grid" aria-label={t("downloadableResources")}>
          {resources.map((resource) => (
            <ResourceCard key={resource.id} language={language} resource={resource} t={t} />
          ))}
        </section>
      )}
    </>
  );
}

function EducationChat({ language, t }) {
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      content: t("chatWelcome"),
      sources: [],
    },
  ]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const messagesRef = useRef(null);

  useEffect(() => {
    if (!messagesRef.current) return;
    messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
  }, [messages]);

  useEffect(() => {
    setMessages((items) =>
      items.map((item) => (item.id === "welcome" ? { ...item, content: t("chatWelcome") } : item)),
    );
  }, [t]);

  async function submit(event) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || sending) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      sources: [],
    };
    const pendingId = `assistant-${Date.now()}`;
    const history = messages
      .filter((item) => item.role === "user" || item.role === "assistant")
      .map((item) => ({ role: item.role, content: item.content }))
      .slice(-8);

    setMessages((items) => [
      ...items,
      userMessage,
      { id: pendingId, role: "assistant", content: t("searchingEducation"), sources: [], pending: true },
    ]);
    setDraft("");
    setSending(true);
    setError("");

    try {
      const payload = await apiFetch("/api/chat/", {
        method: "POST",
        body: JSON.stringify({ message: content, history, language }),
      });
      setMessages((items) =>
        items.map((item) =>
          item.id === pendingId
            ? {
                ...item,
                content: payload.reply,
                sources: payload.sources || [],
                provider: payload.provider,
                model: payload.model,
                reasoningEffort: payload.reasoningEffort,
                pending: false,
              }
            : item,
        ),
      );
    } catch (err) {
      setMessages((items) =>
        items.map((item) =>
          item.id === pendingId
            ? {
                ...item,
                content: translateApiError(err.message, language),
                sources: [],
                pending: false,
                error: true,
              }
            : item,
        ),
      );
      setError(translateApiError(err.message, language));
    } finally {
      setSending(false);
    }
  }

  return (
    <section className="chat-workspace" aria-label={t("chatAria")}>
      <div className="chat-thread" ref={messagesRef}>
        {messages.map((message) => (
          <article className={`chat-message ${message.role} ${message.error ? "error" : ""}`} key={message.id}>
            <div className="chat-bubble">
              {message.pending && <LoaderCircle className="spin" size={18} />}
              {message.model && !message.error && (
                <small className="model-badge">
                  {message.provider || "OpenAI"} {message.model} - {message.reasoningEffort} {t("reasoning")}
                </small>
              )}
              <MarkdownMessage content={message.content} />
              {message.sources?.length > 0 && <ChatSources sources={message.sources} t={t} />}
            </div>
          </article>
        ))}
      </div>

      <form className="chat-composer" onSubmit={submit}>
        {error && <p className="notice error">{error}</p>}
        <label className="chat-input">
          <textarea
            rows={3}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                submit(event);
              }
            }}
            placeholder={t("chatPlaceholder")}
          />
        </label>
        <button className="primary-button send-button" disabled={sending || !draft.trim()} type="submit">
          {sending ? <LoaderCircle className="spin" size={17} /> : <Send size={17} />}
          {t("send")}
        </button>
      </form>
    </section>
  );
}

function MarkdownMessage({ content }) {
  return (
    <div className="markdown-content">
      <ReactMarkdown components={{ a: MarkdownLink }} remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  );
}

function MarkdownLink({ node: _node, href = "", children, ...props }) {
  const targetHref = href.trim();
  const isExternal = /^https?:\/\//i.test(targetHref);
  const isInternal = targetHref.startsWith("/");

  if (!isExternal && !isInternal) {
    return <span>{children}</span>;
  }

  return (
    <a {...props} href={targetHref} rel={isExternal ? "noreferrer" : undefined} target={isExternal ? "_blank" : undefined}>
      {children}
    </a>
  );
}

function ChatSources({ sources, t }) {
  return (
    <div className="chat-sources" aria-label={t("answerSources")}>
      {sources.map((source) => {
        const locator = source.locator || "";
        const href = locator.startsWith("http") ? locator : locator.startsWith("/") ? `${API_BASE}${locator}` : "";
        if (!href) {
          return (
            <span className="source-pill" key={`${source.kind}-${source.title}`}>
              {source.title}
            </span>
          );
        }
        return (
          <a href={href} key={`${source.kind}-${source.locator}`} rel="noreferrer" target="_blank">
            {source.title}
          </a>
        );
      })}
    </div>
  );
}

function SettingsPage({ language, t }) {
  const [sources, setSources] = useState([]);
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function loadSources() {
      setLoading(true);
      setError("");
      try {
        const payload = await apiFetch("/api/chat/sources/");
        if (active) setSources(payload.sources || []);
      } catch (err) {
        if (active) setError(translateApiError(err.message, language));
      } finally {
        if (active) setLoading(false);
      }
    }

    loadSources();
    return () => {
      active = false;
    };
  }, []);

  async function addSource(event) {
    event.preventDefault();
    if (!url.trim()) return;
    setSaving(true);
    setError("");

    try {
      const payload = await apiFetch("/api/chat/sources/create/", {
        method: "POST",
        body: JSON.stringify({ title, url }),
      });
      setSources((items) => [payload.source, ...items]);
      setTitle("");
      setUrl("");
    } catch (err) {
      setError(translateApiError(err.message, language));
    } finally {
      setSaving(false);
    }
  }

  async function toggleSource(source) {
    setError("");
    try {
      const payload = await apiFetch(`/api/chat/sources/${source.id}/update/`, {
        method: "POST",
        body: JSON.stringify({ isActive: !source.isActive }),
      });
      setSources((items) => items.map((item) => (item.id === source.id ? payload.source : item)));
    } catch (err) {
      setError(translateApiError(err.message, language));
    }
  }

  async function deleteSource(source) {
    setError("");
    try {
      await apiFetch(`/api/chat/sources/${source.id}/delete/`, { method: "POST" });
      setSources((items) => items.filter((item) => item.id !== source.id));
    } catch (err) {
      setError(translateApiError(err.message, language));
    }
  }

  return (
    <section className="settings-workspace" aria-label={t("settingsAria")}>
      <form className="settings-form" onSubmit={addSource}>
        <div>
          <p className="eyebrow">{t("chatSourcesEyebrow")}</p>
          <h2>{t("addWebsiteSource")}</h2>
        </div>
        <label>
          {t("label")}
          <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder={t("gmlsEducationPage")} />
        </label>
        <label>
          {t("websiteUrl")}
          <input
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://example.org/education"
            type="url"
          />
        </label>
        {error && <p className="notice error">{error}</p>}
        <button className="primary-button" disabled={saving || !url.trim()} type="submit">
          {saving ? <LoaderCircle className="spin" size={17} /> : <Plus size={17} />}
          {t("addWebsite")}
        </button>
      </form>

      <section className="source-list" aria-label={t("configuredWebsiteSources")}>
        <div className="source-list-header">
          <h2>{t("websiteSources")}</h2>
          {loading && <LoaderCircle className="spin" size={18} />}
        </div>
        {!loading && sources.length === 0 ? (
          <p className="queue-empty">{t("noWebsiteSources")}</p>
        ) : (
          sources.map((source) => (
            <article className="source-item" key={source.id}>
              <div>
                <h3>{source.title || source.url}</h3>
                <a href={source.url} rel="noreferrer" target="_blank">
                  {source.url}
                </a>
              </div>
              <label className="source-toggle">
                <input checked={source.isActive} onChange={() => toggleSource(source)} type="checkbox" />
                <span>{source.isActive ? t("sourceActive") : t("sourceInactive")}</span>
              </label>
              <button className="icon-button danger" onClick={() => deleteSource(source)} type="button">
                <Trash2 size={17} />
              </button>
            </article>
          ))
        )}
      </section>
    </section>
  );
}

function ChecklistGenerator({ language, t }) {
  const [queue, setQueue] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [processingId, setProcessingId] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [previewUrls, setPreviewUrls] = useState({});
  const [previewLoadingId, setPreviewLoadingId] = useState("");
  const [previewError, setPreviewError] = useState({ id: "", message: "" });
  const [aiAcknowledged, setAiAcknowledged] = useState(false);
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
        if (active) setLoadError(translateApiError(err.message, language));
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

    const nextItem = queue.find((item) => item.status === "pending" && item.file);
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
          items.map((item) =>
            item.id === nextItem.id
              ? { ...item, status: "error", error: translateApiError(err.message, language) }
              : item,
          ),
        );
        setSelectedId((current) => current || nextItem.id);
      })
      .finally(() => {
        setProcessingId(null);
      });
  }, [language, processingId, queue]);

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

    fetchPdfBlobUrl(selectedItem.previewUrl, language)
      .then((url) => {
        if (!active) {
          window.URL.revokeObjectURL(url);
          return;
        }
        previewUrlsRef.current = { ...previewUrlsRef.current, [selectedItem.id]: url };
        setPreviewUrls((current) => ({ ...current, [selectedItem.id]: url }));
      })
      .catch((err) => {
        if (active) setPreviewError({ id: selectedItem.id, message: translateApiError(err.message, language) });
      })
      .finally(() => {
        previewRequestsRef.current.delete(selectedItem.id);
        if (active) setPreviewLoadingId("");
      });

    return () => {
      active = false;
    };
  }, [language, previewUrls, selectedItem]);

  function addFiles(fileList) {
    if (!aiAcknowledged) {
      setLoadError(t("confirmAiBeforeFiles"));
      return;
    }
    const files = Array.from(fileList || []).filter((item) => item.name.toLowerCase().endsWith(".docx"));
    if (files.length === 0) return;

    const newItems = files.map((item) => ({
      id: `${Date.now()}-${item.name}-${Math.random().toString(16).slice(2)}`,
      file: item,
      aiProcessingAcknowledged: aiAcknowledged,
      inputFilename: item.name,
      language,
      status: "pending",
      error: "",
      outputFilename: language === "id" ? "daftar-periksa-relawan.pdf" : "volunteer-checklist.pdf",
      previewUrl: "",
      downloadUrl: "",
    }));

    setLoadError("");
    setQueue((items) => [...newItems, ...items]);
    setSelectedId(newItems[0].id);
  }

  async function downloadSelected() {
    if (!selectedItem?.downloadUrl) return;
    try {
      const url = await fetchPdfBlobUrl(selectedItem.downloadUrl, language);
      downloadUrl(url, selectedItem.outputFilename);
      window.setTimeout(() => window.URL.revokeObjectURL(url), 1000);
    } catch (err) {
      setPreviewError({ id: selectedItem.id, message: translateApiError(err.message, language) });
    }
  }

  return (
    <section className="generator-workspace" aria-label={t("generatorAria")}>
      <div className="generator-panel">
        <div>
          <p className="eyebrow">{t("aiChecklistGenerator")}</p>
          <h2>{t("uploadConceptNotes")}</h2>
          <p>{t("generatorDescription")}</p>
        </div>

        <div className="upload-form">
          {loadError && <p className="notice error">{loadError}</p>}
          <label className="consent-check">
            <input
              checked={aiAcknowledged}
              onChange={(event) => setAiAcknowledged(event.target.checked)}
              type="checkbox"
            />
            <span>{t("aiAcknowledgement")}</span>
          </label>
          <label className="upload-dropzone">
            <Upload size={26} />
            <span>{t("addDocxFiles")}</span>
            <input
              accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              disabled={!aiAcknowledged}
              multiple
              onChange={(event) => {
                addFiles(event.target.files);
                event.target.value = "";
              }}
              type="file"
            />
          </label>

          <div className="queue-stats" aria-label={t("queueStatus")}>
            <SummaryItem icon={<LoaderCircle />} label={t("processing")} value={processingCount} />
            <SummaryItem icon={<FileText />} label={t("waiting")} value={pendingCount} />
            <SummaryItem icon={<FileCheck2 />} label={t("ready")} value={doneCount} />
          </div>
        </div>
      </div>

      <div className="queue-layout">
        <aside className="queue-list" aria-label={t("queueAria")}>
          <div className="queue-list-header">
            <FilePlus2 size={19} />
            <h2>{t("processingQueue")}</h2>
          </div>

          {queue.length === 0 ? (
            <p className="queue-empty">{t("noQueuedDocuments")}</p>
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
                  <small>{getQueueStatusLabel(item, t)}</small>
                  <small>
                    {t("uploadedLanguage", {
                      language: t(LANGUAGES.find((languageItem) => languageItem.value === item.language)?.labelKey || "languageEnglish"),
                    })}
                  </small>
                  {item.expiresAt && <small>{t("expires", { time: formatQueueTime(item.expiresAt, item.language) })}</small>}
                </span>
              </button>
            ))
          )}
        </aside>

        <section className="preview-panel" aria-label={t("previewAria")}>
          {!selectedItem ? (
            <div className="preview-empty">
              <Eye size={32} />
              <h2>{t("previewWillAppear")}</h2>
              <p>{t("emptyGenerator")}</p>
            </div>
          ) : selectedItem.status === "done" ? (
            <>
              <div className="preview-header">
                <div>
                  <p className="eyebrow">{t("pdfPreview")}</p>
                  <h2>{selectedItem.outputFilename}</h2>
                </div>
                <button className="download-button" onClick={downloadSelected} type="button">
                  <Download size={17} />
                  {t("download")}
                </button>
              </div>
              {previewError.id === selectedItem.id ? (
                <div className="preview-empty">
                  <FileText size={32} />
                  <h2>{t("previewUnavailable")}</h2>
                  <p>{previewError.message}</p>
                </div>
              ) : previewUrls[selectedItem.id] ? (
                <iframe className="pdf-preview" src={previewUrls[selectedItem.id]} title={selectedItem.outputFilename} />
              ) : (
                <div className="preview-empty">
                  <LoaderCircle className="spin" size={32} />
                  <h2>{t("loadingPreview")}</h2>
                  <p>{t("preparingPreview")}</p>
                </div>
              )}
            </>
          ) : (
            <div className="preview-empty">
              {selectedItem.status === "error" ? <FileText size={32} /> : <LoaderCircle className="spin" size={32} />}
              <h2>{selectedItem.inputFilename}</h2>
              <p>{selectedItem.status === "error" ? selectedItem.error : getQueueStatusLabel(selectedItem, t)}</p>
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
  formData.append("ai_processing_acknowledged", item.aiProcessingAcknowledged ? "true" : "false");
  formData.append("language", item.language || "en");

  const response = await fetch(`${API_BASE}/api/checklists/jobs/create/`, {
    method: "POST",
    credentials: "include",
    headers: {
      ...getAuthHeaders(),
      "X-CSRFToken": getCsrfToken(),
    },
    body: formData,
  });

  const payload = await response.json().catch(() => ({}));
  if (payload.job) return payload.job;
  if (!response.ok) throw new Error(payload.detail || "Checklist generation failed.");
  throw new Error("Checklist generation returned an invalid response.");
}

async function fetchPdfBlobUrl(path, language) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(translateApiError(payload.detail || "Could not load the generated PDF.", language));
  }

  const blob = await response.blob();
  return window.URL.createObjectURL(blob);
}

async function downloadProtectedFile(path, fallbackFilename, language) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(translateApiError(payload.detail || "Could not download the file.", language));
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  downloadUrl(url, getFilenameFromDisposition(response.headers.get("Content-Disposition")) || fallbackFilename);
  window.setTimeout(() => window.URL.revokeObjectURL(url), 1000);
}

function getFilenameFromDisposition(value) {
  const match = value?.match(/filename="?([^"]+)"?/i);
  return match?.[1];
}

function getQueueStatusLabel(item, t) {
  if (item.status === "pending") return t("statusPending");
  if (item.status === "processing") return t("statusProcessing");
  if (item.status === "done") return t("statusDone");
  return item.error || t("errorGenerationFailed");
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
    language: job.language || "en",
    status: job.status,
    error: job.error || "",
    previewUrl: job.previewUrl || "",
    downloadUrl: job.downloadUrl || "",
    expiresAt: job.expiresAt,
  };
}

function formatQueueTime(value, language) {
  return new Intl.DateTimeFormat(localeForLanguage(language), {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function LoginScreen({ language, onLanguageChange, onLogin, t }) {
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
      setError(translateApiError(err.message, language));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="login-header">
          <div className="login-title">
            <BrandMarks />
            <div>
              <p className="eyebrow">{t("loginEyebrow")}</p>
              <h1>{t("signInHeading")}</h1>
            </div>
          </div>
          <LanguageToggle language={language} onChange={onLanguageChange} t={t} />
        </div>
        <form onSubmit={submit}>
          <label>
            {t("username")}
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" />
          </label>
          <label>
            {t("password")}
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              autoComplete="current-password"
            />
          </label>
          {error && <p className="notice error">{error}</p>}
          <button className="primary-button" disabled={submitting} type="submit">
            {submitting ? t("signInLoading") : t("signIn")}
          </button>
        </form>
      </section>
    </main>
  );
}

function BrandMarks({ compact = false }) {
  return (
    <span className={`brand-marks${compact ? " compact" : ""}`}>
      {ORGANIZATION_LOGOS.map((logo) => (
        <span className="brand-mark" key={logo.src}>
          <img src={logo.src} alt={logo.alt} />
        </span>
      ))}
    </span>
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

function ResourceCard({ language, resource, t }) {
  const uploaded = new Intl.DateTimeFormat(localeForLanguage(language), { dateStyle: "medium" }).format(
    new Date(resource.uploadedAt),
  );
  const categoryLabel = resource.category === "checklist" ? t("categoryChecklist") : t("categoryEducational");

  return (
    <article className="resource-card">
      <div className="card-header">
        <span className={`category-pill ${resource.category}`}>{categoryLabel}</span>
        <span className="file-type">{resource.fileType}</span>
        <FileText size={22} />
      </div>
      <h2>{resource.title}</h2>
      <p>{resource.description || t("fileNoDescription")}</p>
      <div className="card-footer">
        <span>{t("fileUploaded", { date: uploaded })}</span>
        <button
          className="download-button"
          onClick={() => downloadProtectedFile(resource.downloadUrl, resource.title, language)}
          type="button"
        >
          <Download size={17} />
          {t("download")}
        </button>
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
