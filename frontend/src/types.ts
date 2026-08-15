export type Language = "en" | "zh" | "tw";
export type GroupingMode = "date" | "topic";

export interface LocalizedText {
  en: string;
  zh: string;
  tw: string;
}

export interface Article {
  id: string;
  date: string;
  year: string;
  topic: string;
  author: string;
  url: string;
  pdfUrl?: string;
  title: LocalizedText;
  description: LocalizedText;
  body: LocalizedText;
  keyIdea: LocalizedText;
}

export interface ApiArticle {
  id: string;
  title: string;
  author: string;
  url: string;
  created_at: string;
  updated_at: string;
}

export interface HistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export interface Citation {
  article_id: string;
  title: string;
  url: string;
  excerpt: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  insufficient_evidence: boolean;
}

export interface ChatTurn {
  id: string;
  question: string;
  status: "loading" | "complete" | "error";
  response?: ChatResponse;
  error?: string;
}
