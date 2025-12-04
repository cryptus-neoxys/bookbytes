import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

export interface Book {
  isbn: string;
  title: string;
  author: string;
  pages?: number;
  publish_date?: string;
  chapter_count?: number;
}

export interface Chapter {
  chapter_number: number;
  title: string;
  summary: string;
  audio_file_path?: string;
  word_count?: number;
  has_audio: boolean;
}

export interface ProcessBookResponse {
  success: boolean;
  message: string;
  book: Book;
  chapters_processed: number;
  request_id: string;
  processing_time: string;
}

export interface GetBooksResponse {
  books: Book[];
  count: number;
  request_id: string;
  processing_time: string;
}

export interface GetChaptersResponse {
  chapters: Chapter[];
  count: number;
  isbn: string;
  request_id: string;
  processing_time: string;
}

export const processBook = async (
  isbn: string
): Promise<ProcessBookResponse> => {
  const response = await api.post<ProcessBookResponse>("/process", { isbn });
  return response.data;
};

export const getBooks = async (): Promise<GetBooksResponse> => {
  const response = await api.get<GetBooksResponse>("/books");
  return response.data;
};

export interface GetBookResponse {
  book: Book;
  request_id: string;
  processing_time: string;
}

export const getBook = async (isbn: string): Promise<GetBookResponse> => {
  const response = await api.get<GetBookResponse>(`/books/${isbn}`);
  return response.data;
};

export const getChapters = async (
  isbn: string
): Promise<GetChaptersResponse> => {
  const response = await api.get<GetChaptersResponse>(
    `/books/${isbn}/chapters`
  );
  return response.data;
};

export default api;
