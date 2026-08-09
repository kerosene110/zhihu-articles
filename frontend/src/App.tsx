import {
  ArrowUpRight,
  BookOpenText,
  Bot,
  CalendarDays,
  ChevronDown,
  Database,
  FileText,
  Layers3,
  Menu,
  MessageSquare,
  Search,
  Send,
  Sparkles,
  Tag,
  X,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { askQuestion, fetchArticles } from "./api";
import { articles as referenceArticles, uiCopy } from "./data";
import type {
  ApiArticle,
  Article,
  ChatTurn,
  GroupingMode,
  HistoryMessage,
  Language,
} from "./types";

const languageOptions: { value: Language; label: string }[] = [
  { value: "en", label: "EN" },
  { value: "zh", label: "简" },
  { value: "tw", label: "繁" },
];

const suggestedQuestions = [
  "Why does implied volatility often collapse after earnings?",
  "如何理解 Delta 中性策略的主要风险？",
  "When does portfolio convexity justify its recurring cost?",
];

function readableDate(value?: string): string {
  if (!value) return "Undated";
  return value.slice(0, 10);
}

function apiArticleToArticle(item: ApiArticle, index: number): Article {
  const date = readableDate(item.created_at ?? item.creation_date ?? item.updated_at ?? item.update_date);
  const title = item.title || `Article ${index + 1}`;
  return {
    id: String(item.article_id ?? item.id ?? index),
    date,
    year: date === "Undated" ? "Archive" : date.slice(0, 4),
    topic: "Xuzhe Finance",
    author: item.author,
    url: item.url,
    title: { en: title, zh: title, tw: title },
    description: {
      en: "This article is available in the indexed Xuzhe corpus. Ask the study assistant for a grounded explanation with source excerpts.",
      zh: "该文章已收录在徐哲语料库中。可向学习助手提问，并获得带原文摘录的回答。",
      tw: "該文章已收錄在徐哲語料庫中。可向學習助手提問，並獲得附原文摘錄的回答。",
    },
    body: {
      en: "The original article remains in Chinese. Use the source link to read it in full, or ask a question to retrieve the most relevant passages.",
      zh: "原始文章保留中文内容。请打开知乎原文阅读全文，或通过提问检索最相关的段落。",
      tw: "原始文章保留中文內容。請開啟知乎原文閱讀全文，或透過提問檢索最相關的段落。",
    },
    keyIdea: {
      en: "Use grounded questions to connect this article to the wider corpus without introducing unsupported claims.",
      zh: "通过有出处的问题把本文与整个语料库关联起来，同时避免无依据的结论。",
      tw: "透過有出處的問題把本文與整個語料庫關聯起來，同時避免無依據的結論。",
    },
  };
}

function loadStoredTurns(): ChatTurn[] {
  try {
    const value = sessionStorage.getItem("xuzhe-chat-history");
    return value ? (JSON.parse(value) as ChatTurn[]) : [];
  } catch {
    return [];
  }
}

function PayoffChart({ iv, dte }: { iv: number; dte: number }) {
  const width = 680;
  const height = 220;
  const padding = { top: 18, right: 18, bottom: 32, left: 38 };
  const minPrice = 100;
  const maxPrice = 200;
  const minPayoff = -28;
  const maxPayoff = 44;
  const premium = 12 * Math.sqrt(dte / 30) * (iv / 45);
  const x = (price: number) =>
    padding.left + ((price - minPrice) / (maxPrice - minPrice)) * (width - padding.left - padding.right);
  const y = (payoff: number) =>
    padding.top + ((maxPayoff - payoff) / (maxPayoff - minPayoff)) * (height - padding.top - padding.bottom);
  const points = Array.from({ length: 51 }, (_, index) => {
    const price = minPrice + index * 2;
    const payoff = Math.abs(price - 150) - premium;
    return `${x(price)},${y(payoff)}`;
  }).join(" ");
  const areaPoints = `${x(minPrice)},${y(0)} ${points} ${x(maxPrice)},${y(0)}`;
  const ticks = [-20, 0, 20, 40];

  return (
    <svg
      className="payoff-svg"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={`Long straddle payoff chart with ${iv}% implied volatility and ${dte} days to expiration`}
    >
      <defs>
        <linearGradient id="payoff-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#10b981" stopOpacity=".18" />
          <stop offset="100%" stopColor="#10b981" stopOpacity=".025" />
        </linearGradient>
      </defs>
      {ticks.map((tick) => (
        <g key={tick}>
          <line x1={padding.left} x2={width - padding.right} y1={y(tick)} y2={y(tick)} className="chart-grid" />
          <text x={padding.left - 9} y={y(tick) + 4} textAnchor="end" className="chart-label">
            {tick}
          </text>
        </g>
      ))}
      <line x1={padding.left} x2={width - padding.right} y1={y(0)} y2={y(0)} className="chart-zero" />
      <polygon points={areaPoints} fill="url(#payoff-fill)" />
      <polyline points={points} className="chart-line" />
      {[100, 125, 150, 175, 200].map((price) => (
        <text key={price} x={x(price)} y={height - 9} textAnchor="middle" className="chart-label">
          ${price}
        </text>
      ))}
    </svg>
  );
}

function App() {
  const [language, setLanguage] = useState<Language>("en");
  const [grouping, setGrouping] = useState<GroupingMode>("date");
  const [allArticles, setAllArticles] = useState<Article[]>(referenceArticles);
  const [selectedId, setSelectedId] = useState(referenceArticles[0].id);
  const [search, setSearch] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>(loadStoredTurns);
  const [iv, setIv] = useState(45);
  const [dte, setDte] = useState(30);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const copy = uiCopy[language];

  useEffect(() => {
    if (import.meta.env.DEV && !import.meta.env.VITE_API_BASE_URL) return;
    const controller = new AbortController();
    fetchArticles(controller.signal)
      .then((items) => {
        if (!items.length) return;
        const mapped = items.map(apiArticleToArticle);
        setAllArticles(mapped);
        setSelectedId(mapped[0].id);
      })
      .catch(() => {
        // The reference set keeps the frontend reviewable until the API is running.
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    sessionStorage.setItem("xuzhe-chat-history", JSON.stringify(turns));
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [turns]);

  useEffect(() => {
    if (!chatOpen && !sidebarOpen) return;
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setChatOpen(false);
        setSidebarOpen(false);
      }
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [chatOpen, sidebarOpen]);

  const selectedArticle = allArticles.find((article) => article.id === selectedId) ?? allArticles[0];
  const filteredArticles = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    if (!query) return allArticles;
    return allArticles.filter((article) =>
      [article.title.en, article.title.zh, article.title.tw, article.topic, article.body.en, article.body.zh]
        .join(" ")
        .toLocaleLowerCase()
        .includes(query),
    );
  }, [allArticles, search]);

  const articleGroups = useMemo(() => {
    const groups = new Map<string, Article[]>();
    filteredArticles.forEach((article) => {
      const key = grouping === "date" ? article.year : article.topic;
      groups.set(key, [...(groups.get(key) ?? []), article]);
    });
    return [...groups.entries()];
  }, [filteredArticles, grouping]);

  async function submitQuestion(nextQuestion = question) {
    const trimmed = nextQuestion.trim();
    if (!trimmed) return;
    const id = crypto.randomUUID();
    const previousHistory: HistoryMessage[] = turns.flatMap((turn) => {
      if (turn.status !== "complete" || !turn.response) return [];
      return [
        { role: "user" as const, content: turn.question },
        { role: "assistant" as const, content: turn.response.answer },
      ];
    });

    setQuestion("");
    setTurns((current) => [...current, { id, question: trimmed, status: "loading" }]);
    try {
      const response = await askQuestion(trimmed, previousHistory.slice(-8));
      setTurns((current) => current.map((turn) => (turn.id === id ? { ...turn, status: "complete", response } : turn)));
    } catch {
      setTurns((current) =>
        current.map((turn) =>
          turn.id === id
            ? {
                ...turn,
                status: "error",
                error: "The grounded-answer service is unavailable. Start the FastAPI server and try again.",
              }
            : turn,
        ),
      );
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    void submitQuestion();
  }

  function selectArticle(id: string) {
    setSelectedId(id);
    setSidebarOpen(false);
    document.querySelector(".article-scroll")?.scrollTo({ top: 0, behavior: "smooth" });
  }

  if (!selectedArticle) return null;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="corpus-meta">
          <button className="icon-button mobile-menu" onClick={() => setSidebarOpen(true)} aria-label="Open article navigation">
            <Menu size={18} />
          </button>
          <div className="corpus-badge">
            <Database size={14} aria-hidden="true" />
            <span>RAG Corpus: Zhihu / Xuzhe Finance</span>
          </div>
          <span className="article-count">{allArticles.length} Articles</span>
        </div>
        <label className="search-box">
          <Search size={16} aria-hidden="true" />
          <span className="sr-only">Search articles</span>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={copy.search} />
          <span className="search-mode"><Sparkles size={11} /> Hybrid RAG</span>
        </label>
      </header>

      <div className="workspace">
        {sidebarOpen && <button className="scrim sidebar-scrim" onClick={() => setSidebarOpen(false)} aria-label="Close article navigation" />}
        <aside className={`sidebar ${sidebarOpen ? "is-open" : ""}`} aria-label="Article navigation">
          <div className="sidebar-content">
            <div className="sidebar-heading-row">
              <div>
                <p className="eyebrow">Study Companion</p>
                <h1>Xuzhe Options &amp; Macro</h1>
                <p className="sidebar-subtitle">US Stock Trading &amp; Hedging Frameworks</p>
                <p className="author-line">Author: Xuzhe (知乎 @徐哲)</p>
              </div>
              <button className="icon-button sidebar-close" onClick={() => setSidebarOpen(false)} aria-label="Close article navigation">
                <X size={18} />
              </button>
            </div>

            <div className="segmented language-toggle" aria-label="Language">
              {languageOptions.map((option) => (
                <button
                  key={option.value}
                  className={language === option.value ? "active" : ""}
                  onClick={() => setLanguage(option.value)}
                  aria-pressed={language === option.value}
                >
                  {option.label}
                </button>
              ))}
            </div>

            <div className="group-controls">
              <div className="section-label"><span>Group articles by</span><Layers3 size={13} /></div>
              <div className="segmented grouping-toggle">
                <button className={grouping === "date" ? "active" : ""} onClick={() => setGrouping("date")} aria-pressed={grouping === "date"}>
                  <CalendarDays size={13} /> By Date
                </button>
                <button className={grouping === "topic" ? "active" : ""} onClick={() => setGrouping("topic")} aria-pressed={grouping === "topic"}>
                  <Tag size={13} /> By Topic
                </button>
              </div>
            </div>

            <nav className="article-nav">
              {articleGroups.length === 0 && <p className="empty-search">No articles match “{search}”.</p>}
              {articleGroups.map(([group, items]) => (
                <section className="article-group" key={group}>
                  <div className="group-label">
                    <span>{grouping === "topic" && <Tag size={11} />}{group}</span>
                    <span>{items.length} {items.length === 1 ? "article" : "articles"}</span>
                  </div>
                  <div className="article-list">
                    {items.map((article) => (
                      <button
                        key={article.id}
                        className={`article-link ${selectedArticle.id === article.id ? "active" : ""}`}
                        onClick={() => selectArticle(article.id)}
                        aria-current={selectedArticle.id === article.id ? "page" : undefined}
                      >
                        <span className="article-link-meta">
                          <span>{article.date}</span>
                          <span>{article.topic.split(" ")[0]}</span>
                        </span>
                        <span className="article-link-title">{article.title[language]}</span>
                      </button>
                    ))}
                  </div>
                </section>
              ))}
            </nav>
          </div>
          <div className="sidebar-footer">
            <a className="feedback-button" href="mailto:feedback@example.com"><MessageSquare size={14} /> Feedback</a>
          </div>
        </aside>

        <main className="article-scroll" id="main-content">
          <article className="article-content">
            <header className="article-header">
              <div className="breadcrumb"><span>{selectedArticle.topic}</span><span>•</span><time>{selectedArticle.date}</time></div>
              <h2>{selectedArticle.title[language]}</h2>
              <p>{selectedArticle.description[language]}</p>
              <div className="article-actions">
                <a href={selectedArticle.url} target="_blank" rel="noreferrer"><ArrowUpRight size={14} /> {copy.source}</a>
                {selectedArticle.pdfUrl && <a href={selectedArticle.pdfUrl} target="_blank" rel="noreferrer"><FileText size={14} /> Read the full article in PDF</a>}
              </div>
            </header>

            <section className="model-card" aria-labelledby="model-heading">
              <div className="model-heading">
                <div><span className="status-dot" /><h3 id="model-heading">Interactive model: Long straddle vs IV smile</h3></div>
                <p>Spot S₀ = $150 <span>•</span> Strike K = $150</p>
              </div>
              <div className="chart-frame"><PayoffChart iv={iv} dte={dte} /></div>
              <div className="sliders">
                <label>
                  <span><span>Implied Volatility (IV):</span><output>{iv}%</output></span>
                  <input type="range" min="10" max="100" value={iv} onChange={(event) => setIv(Number(event.target.value))} />
                </label>
                <label>
                  <span><span>Days to Expiration (DTE):</span><output>{dte} Days</output></span>
                  <input type="range" min="1" max="90" value={dte} onChange={(event) => setDte(Number(event.target.value))} />
                </label>
              </div>
            </section>

            <aside className="key-idea">
              <p>Key idea</p>
              <div>{selectedArticle.keyIdea[language]}</div>
            </aside>

            <section className="study-copy">
              <div className="source-label"><BookOpenText size={15} /> Indexed source note</div>
              <p key={`${selectedArticle.id}-${language}`}>{selectedArticle.body[language]}</p>
            </section>
          </article>
        </main>

        <button className="chat-trigger" onClick={() => setChatOpen(true)} aria-haspopup="dialog" aria-label={copy.ask}>
          <Sparkles size={16} /> <span>{copy.ask}</span>
        </button>

        {chatOpen && <button className="scrim chat-scrim" onClick={() => setChatOpen(false)} aria-label="Close assistant" />}
        <aside className={`chat-drawer ${chatOpen ? "is-open" : ""}`} role="dialog" aria-modal="true" aria-labelledby="chat-title">
          <header className="chat-header">
            <div><h2 id="chat-title">{copy.drawerTitle}</h2><p>{copy.drawerSubtitle}</p></div>
            <button className="icon-button" onClick={() => setChatOpen(false)} aria-label="Close assistant"><X size={18} /></button>
          </header>
          <div className="chat-body">
            <form className="ask-form" onSubmit={handleSubmit}>
              <label><span className="sr-only">Your question</span><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={copy.question} /></label>
              <button type="submit" disabled={!question.trim()}><Send size={14} /> Ask</button>
            </form>
            <p className="grounding-note">Answers use only retrieved corpus passages. Every source link opens the original Chinese article.</p>

            {turns.length === 0 && (
              <section className="suggestions">
                <p>Suggested queries</p>
                {suggestedQuestions.map((suggestion) => (
                  <button key={suggestion} onClick={() => void submitQuestion(suggestion)}>“{suggestion}”</button>
                ))}
              </section>
            )}

            <div className="chat-history" aria-live="polite">
              {turns.map((turn) => (
                <div className="chat-turn" key={turn.id}>
                  <div className="user-message"><span>You</span><p>{turn.question}</p></div>
                  {turn.status === "loading" && (
                    <div className="assistant-message loading"><div className="answer-heading"><Sparkles size={14} /><span>Retrieving Zhihu passages…</span></div><p>Comparing the question with the indexed corpus.</p></div>
                  )}
                  {turn.status === "error" && (
                    <div className="assistant-message error"><div className="answer-heading"><Bot size={14} /><span>Couldn’t reach the corpus</span></div><p>{turn.error}</p><button onClick={() => { setTurns((current) => current.filter((candidate) => candidate.id !== turn.id)); void submitQuestion(turn.question); }}>Try again</button></div>
                  )}
                  {turn.status === "complete" && turn.response && (
                    <div className={`assistant-message ${turn.response.insufficient_evidence ? "insufficient" : ""}`}>
                      <div className="answer-heading"><span><Bot size={14} /> Grounded answer</span><span>{turn.response.citations.length} sources</span></div>
                      <p className="answer-copy">{turn.response.answer}</p>
                      {turn.response.insufficient_evidence && <div className="evidence-warning">The corpus did not contain enough evidence for a supported answer.</div>}
                      {turn.response.citations.length > 0 && (
                        <div className="citations">
                          {turn.response.citations.map((citation, index) => (
                            <details key={`${citation.article_id}-${index}`}>
                              <summary><span>[{index + 1}] {citation.title}</span><ChevronDown size={14} /></summary>
                              <blockquote lang="zh">{citation.excerpt}</blockquote>
                              <a href={citation.url} target="_blank" rel="noreferrer">Open Zhihu source <ArrowUpRight size={12} /></a>
                            </details>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
          </div>
          <footer className="chat-footer">Grounded by the configured RAG pipeline. Follow citations to verify every answer.</footer>
        </aside>
      </div>
    </div>
  );
}

export default App;
