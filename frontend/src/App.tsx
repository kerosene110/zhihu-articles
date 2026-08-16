import {
  Bot,
  Database,
  ExternalLink,
  LoaderCircle,
  Search,
  Send,
  Sparkles,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { askQuestion, fetchArticles } from "./api";
import type { ApiArticle, ChatTurn, HistoryMessage } from "./types";

const suggestions = [
  "Why can apparently safe arbitrage strategies fail?",
  "What does the author say about financial bubbles?",
  "如何理解期权交易中的风险？",
];

function loadStoredTurns(): ChatTurn[] {
  try {
    const stored = sessionStorage.getItem("xuzhe-chat-history");
    return stored ? (JSON.parse(stored) as ChatTurn[]) : [];
  } catch {
    return [];
  }
}

export default function App() {
  const [articles, setArticles] = useState<ApiArticle[]>([]);
  const [articleQuery, setArticleQuery] = useState("");
  const [corpusLoading, setCorpusLoading] = useState(true);
  const [corpusError, setCorpusError] = useState("");
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>(loadStoredTurns);

  useEffect(() => {
    const controller = new AbortController();
    fetchArticles(controller.signal)
      .then(setArticles)
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setCorpusError(
          error instanceof Error ? error.message : "Could not load the corpus.",
        );
      })
      .finally(() => setCorpusLoading(false));
    return () => controller.abort();
  }, []);

  useEffect(() => {
    sessionStorage.setItem("xuzhe-chat-history", JSON.stringify(turns));
  }, [turns]);

  const visibleArticles = useMemo(() => {
    const query = articleQuery.trim().toLocaleLowerCase();
    if (!query) return articles;
    return articles.filter((article) =>
      [article.title, article.author]
        .join(" ")
        .toLocaleLowerCase()
        .includes(query),
    );
  }, [articleQuery, articles]);

  async function submitQuestion(nextQuestion = question) {
    const trimmed = nextQuestion.trim();
    if (!trimmed) return;

    const id = crypto.randomUUID();
    const history: HistoryMessage[] = turns.flatMap((turn) => {
      if (turn.status !== "complete" || !turn.response) return [];
      return [
        { role: "user" as const, content: turn.question },
        { role: "assistant" as const, content: turn.response.answer },
      ];
    });

    setQuestion("");
    setTurns((current) => [
      ...current,
      { id, question: trimmed, status: "loading" },
    ]);

    try {
      const response = await askQuestion(trimmed, history.slice(-8));
      setTurns((current) =>
        current.map((turn) =>
          turn.id === id ? { ...turn, status: "complete", response } : turn,
        ),
      );
    } catch (error) {
      setTurns((current) =>
        current.map((turn) =>
          turn.id === id
            ? {
                ...turn,
                status: "error",
                error:
                  error instanceof Error
                    ? error.message
                    : "The answer service is unavailable.",
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

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark"><Sparkles size={18} /></span>
          <div>
            <strong>Xuzhe RAG</strong>
            <span>Grounded finance study assistant</span>
          </div>
        </div>
        <div className="corpus-status">
          <Database size={15} />
          {corpusLoading ? "Loading corpus…" : `${articles.length} indexed articles`}
        </div>
      </header>

      <main className="workspace">
        <aside className="corpus-panel">
          <div>
            <p className="eyebrow">Source corpus</p>
            <h1>Xu Zhe’s articles</h1>
            <p className="muted">
              Answers are limited to retrieved passages from these Chinese sources.
            </p>
          </div>

          <label className="search-box">
            <Search size={16} />
            <span className="sr-only">Filter articles</span>
            <input
              value={articleQuery}
              onChange={(event) => setArticleQuery(event.target.value)}
              placeholder="Filter titles"
            />
          </label>

          <div className="article-list">
            {corpusLoading && <p className="panel-message">Loading articles…</p>}
            {corpusError && <p className="panel-message error">{corpusError}</p>}
            {!corpusLoading && !corpusError && articles.length === 0 && (
              <p className="panel-message">
                No index is connected yet. Complete ingestion and indexing first.
              </p>
            )}
            {visibleArticles.map((article) => (
              <a
                className="article-link"
                href={article.url}
                key={article.id}
                rel="noreferrer"
                target="_blank"
              >
                <span>{article.title}</span>
                <small>{article.author} · {article.created_at.slice(0, 10)}</small>
                <ExternalLink size={14} />
              </a>
            ))}
          </div>
        </aside>

        <section className="chat-panel" aria-label="Grounded chat">
          <div className="chat-heading">
            <div>
              <p className="eyebrow">Ask the corpus</p>
              <h2>Study with verifiable sources</h2>
            </div>
            <p>Conversation history stays in this browser session.</p>
          </div>

          <div className="conversation" aria-live="polite">
            {turns.length === 0 && (
              <div className="empty-state">
                <span className="empty-icon"><Bot size={30} /></span>
                <h3>Ask a question about the corpus</h3>
                <p>
                  The answer service must cite retrieved Chinese excerpts or say
                  that the evidence is insufficient.
                </p>
                <div className="suggestions">
                  {suggestions.map((suggestion) => (
                    <button key={suggestion} onClick={() => void submitQuestion(suggestion)}>
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {turns.map((turn) => (
              <article className="turn" key={turn.id}>
                <div className="question"><strong>You</strong><p>{turn.question}</p></div>
                {turn.status === "loading" && (
                  <div className="answer loading">
                    <LoaderCircle className="spinner" size={18} />
                    Retrieving evidence…
                  </div>
                )}
                {turn.status === "error" && (
                  <div className="answer error"><strong>Request failed</strong><p>{turn.error}</p></div>
                )}
                {turn.status === "complete" && turn.response && (
                  <div className={`answer ${turn.response.insufficient_evidence ? "insufficient" : ""}`}>
                    <strong>Grounded answer</strong>
                    <p>{turn.response.answer}</p>
                    {turn.response.insufficient_evidence && (
                      <p className="evidence-note">The corpus did not contain enough relevant evidence.</p>
                    )}
                    {turn.response.citations.length > 0 && (
                      <div className="citations">
                        {turn.response.citations.map((citation, index) => (
                          <details key={`${citation.article_id}-${index}`}>
                            <summary>[{index + 1}] {citation.title}</summary>
                            <blockquote>{citation.excerpt}</blockquote>
                            <a href={citation.url} rel="noreferrer" target="_blank">
                              Open original <ExternalLink size={13} />
                            </a>
                          </details>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </article>
            ))}
          </div>

          <form className="composer" onSubmit={handleSubmit}>
            <label htmlFor="question" className="sr-only">Question</label>
            <textarea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder="Ask about risk, arbitrage, options, bubbles…"
              rows={2}
            />
            <button disabled={!question.trim()} type="submit" aria-label="Send question">
              <Send size={18} />
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}
