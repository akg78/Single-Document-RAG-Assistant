export type SourceChunk = {
  id: string;
  page: number;
  chunk_index: number;
  snippet: string;
  score?: number | null;
  source?: string | null;
};

export type QueryRouteInfo = {
  query_type: "single_fact" | "multi_part" | "summarization";
  sub_questions: string[];
};

export type RagasScores = {
  faithfulness?: number | null;
  answer_relevancy?: number | null;
  context_precision?: number | null;
};

export type QueryResponse = {
  answer: string;
  sources: SourceChunk[];
  route: QueryRouteInfo;
  rerank?: {
    pre_rerank: SourceChunk[];
    post_rerank: SourceChunk[];
  } | null;
  ragas?: RagasScores | null;
  document_id?: string | null;
};

export type UploadResponse = {
  document_id: string;
  filename: string;
  num_pages: number;
  num_chunks: number;
  message: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
  ragas?: RagasScores | null;
  route?: QueryRouteInfo;
};
