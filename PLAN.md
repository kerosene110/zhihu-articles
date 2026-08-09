  # RAG assistant For Reading Xu Zhe's Articles

  ## Goal

  Build a RAG application over the approximately 50 structured finance articles -- An interactive way to read and learn.

  The application will accept English questions, retrieve relevant passages from the Chinese corpus using multilingual dense embeddings, and return English answers grounded only in those passages. Citations retain the original Chinese article title, supporting excerpt, and Zhihu URL.

  Preserve the existing crawler commands and PDF-generation behavior. PDFs are not an ingestion source.

  ## Decisions

  1. **Application:** FastAPI with a minimal React/TypeScript frontend.
  2. **Models:** Configurable OpenAI-compatible chat and multilingual embedding endpoints.
  3. **Vector index:** Locally persisted Chroma, chosen for its metadata storage and stable-ID upserts.
  4. **Deployment:** One Dockerized application serving the compiled frontend from FastAPI where practical.
  5. **Answers:** Corpus-grounded only. Insufficient evidence produces an explicit response instead of unsupported model knowledge.
  6. **Language:** Users and the assistant communicate in English or Chinese; source titles, text, excerpts, and links remain in Chinese.
  7. **UI source of truth:** Rendered web-page design drafts supplied in `frontend/design-drafts/` define the intended visual appearance and interaction states. The production frontend should reproduce those drafts closely while preserving accessibility, responsive behavior, and the application contracts in this plan.

  ## Design Draft Contract

  - Treat the rendered drafts, rather than their generated source code or component structure, as the source of truth for layout, typography, color, spacing, imagery, responsive composition, and visible interaction states.
  - Reimplement the designs in the production React/TypeScript application. Do not copy draft-only framework choices, generated code, dependencies, mock APIs, or placeholder business logic unless they are also appropriate for production.
  - Inventory every page, breakpoint, component variant, and state represented in `frontend/design-drafts/` before frontend implementation. Reuse supplied assets where their licensing and format allow it.
  - When drafts disagree with written UI details in this plan, follow the rendered drafts for presentation. Backend behavior, security, data integrity, citation grounding, and explicit API contracts remain governed by this plan.
  - Infer ordinary intermediate responsive behavior from the supplied desktop and mobile views. Record any ambiguity that would materially change navigation, content, or application behavior instead of silently inventing it.
  - Ensure draft fidelity does not compromise semantic HTML, keyboard navigation, focus visibility, readable contrast, reduced-motion preferences, or sensible loading and error announcements.
  - Compare the implementation with the rendered drafts at their reference viewport sizes and cover the comparison with browser screenshots or visual-regression tests for stable, representative states.

  ## Implementation

  ### Ingestion and indexing

  - Define a canonical `Article` model containing the Zhihu article ID, title, author, URL, creation date, update date, and
  cleaned original Chinese text.
  - Define an `ArticleSource` interface so future manual articles and crawler syncs can use the same indexing pipeline.
  - Implement only `SavedMetadataSource` in the MVP.
  - Load both existing metadata formats: top-level arrays and objects containing a `data` array.
  - Deduplicate articles by Zhihu article ID, preferring the record with the longest content and then the latest update
  timestamp.
  - Clean only the Zhihu API `content` field. Preserve headings, paragraphs, and lists as structured plain text.
  - Do not build a generalized HTML-normalization framework.
  - Split articles at structural boundaries into chunks targeting 600 Chinese characters with up to 100 characters of overlap.
  - Generate stable chunk IDs from the article ID, cleaned-content hash, and chunk position.
  - Persist chunks, embeddings, and citation metadata in Chroma.
  - Skip unchanged articles and replace stale chunks when an article changes so repeated ingestion remains idempotent.
  - Provide an indexing CLI with normal, dry-run, and full-rebuild modes.
  - Preserve the current crawler entry points, arguments, and PDF outputs.

  ### Retrieval and answering

  - Embed English questions and Chinese chunks using the same multilingual embedding model.
  - Retrieve the five nearest Chinese chunks, suppress duplicate passages, and enforce a configurable context limit.
  - Calibrate a minimum relevance threshold using the evaluation set.
  - If no passage clears the threshold, return a deterministic English insufficient-evidence response.
  - Instruct the chat model to answer in English using only the retrieved passages.
  - Validate all generated citation IDs against the retrieved chunks.
  - Return original Chinese supporting excerpts without automatic translation.

  ### Backend API

  - `GET /health` returns `{ "status": "ok" }`.
  - `GET /articles` returns indexed article summaries containing ID, Chinese title, author, URL, and dates.
  - `POST /chat` accepts:
    - `question`: the current English question.
    - `history`: optional recent user and assistant messages supplied by the browser.
  - `POST /chat` returns:
    - `answer`: the complete English answer.
    - `citations`: validated citations.
    - `insufficient_evidence`: whether retrieval found adequate support.
  - Each citation contains `article_id`, Chinese `title`, `url`, and original Chinese `excerpt`.
  - Conversation history is never persisted on the server.
  - Keep indexing independent of FastAPI so a protected sync operation can be added later without rewriting ingestion.

  ### Frontend and local delivery

  - Build the responsive pages and navigation represented by the design drafts, with browser-held chat history. Until drafts show otherwise, the MVP requires one chat page.
  - Provide an English question input with loading and error states.
  - Display complete, non-streamed English answers.
  - Render citation markers with expandable cards showing the Chinese title, original excerpt, and Zhihu link.
  - Show a clear insufficient-evidence state when the corpus cannot support an answer.
  - Implement all relevant drafted states, including initial/empty, populated, loading, error, insufficient-evidence, expanded citation, keyboard focus, and narrow-screen layouts.
  - Build reusable production components from repeated visual patterns in the drafts rather than mirroring each draft page as isolated markup.
  - Compile the React application in a Docker multi-stage build and serve its static assets from FastAPI.
  - Persist Chroma through a mounted local volume.
  - Document the workflow: configure credentials, build, run the ingestion CLI, and start the application.
  - Add GitHub Actions checks for backend linting and tests and for a successful frontend build.

  ## Tests and Evaluation

  - Test both saved metadata formats.
  - Test focused HTML extraction and structural text preservation.
  - Test article deduplication, chunk boundaries, and stable chunk IDs.
  - Test initial indexing, unchanged reruns, changed articles, full rebuilds, and duplicate prevention.
  - Test multilingual retrieval using deterministic fake embeddings in CI.
  - Test citation formatting and rejection of fabricated citation IDs.
  - Test successful `/chat` responses, insufficient evidence, provider failures, and bounded history.
  - Verify the frontend production build and core chat and citation rendering.
  - Add browser-level tests for critical user flows and visual comparisons at the reference viewport sizes from `frontend/design-drafts/`.
  - Review visual differences against the drafts before declaring the frontend complete; intentional deviations must be documented with an accessibility, responsiveness, or product-behavior reason.
  - Add a versioned set of 20 representative English questions with expected Chinese article IDs and optional expected
  passage text.
  - Provide an evaluation CLI reporting Hit@1, Hit@5, and mean reciprocal rank.
  - Target at least 85% Hit@5 before declaring the MVP complete.
  - Record the embedding model, chunk settings, retrieval settings, and baseline results in the README.
  - Add crawler compatibility tests that do not make network requests or regenerate corpus files.

  ## Deferred and Excluded

  - Defer manual article ingestion and crawler-backed latest-article sync. Their future implementations must produce the canonical `Article` model and reuse the same indexer.
  - Defer reindexing endpoints, an “Update corpus” button, arbitrary-author crawling, Qdrant, BM25, hybrid retrieval, reranking, streaming, authentication, server-side conversation history, article-browser pages, retrieval-debug panels, extensive observability, and separate liveness/readiness probes.
  - Do not implement PDF ingestion. Existing PDF generation remains supported.