# RAG assistant For Reading Xu Zhe's Articles

A corpus-grounded question-answering application over Xu Zhe's column articles from Zhihu.com.

See [PLAN.md](PLAN.md) for the application design and implementation plan.

## Project modules

- [Crawler](crawler/README.md): existing Zhihu metadata and PDF-generation tools.
- [Frontend](frontend/): responsive React/TypeScript study companion based on the rendered design drafts.

## Frontend development

The frontend can be reviewed before the backend is available; it uses a small reference article set for the visual states. Chat requests still fail closed unless a compatible API is running.

```bash
cd frontend
npm install
npm run dev
```

The Vite development server proxies `/api/articles` and `/api/chat` to `http://127.0.0.1:8000`. Set `VITE_API_BASE_URL` to use a different API base. In a production build, requests default to the same origin so FastAPI can serve both the API and compiled frontend.

```bash
cd frontend
npm run build
```
