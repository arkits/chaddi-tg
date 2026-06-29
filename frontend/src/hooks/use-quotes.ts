import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface Quote {
  quote_id: string;
  created: string;
  text: string;
  author_bakchod: string;
  quoted_in_group: string;
  quote_capture_bakchod: string;
}

export interface QuotesResponse {
  current_page: number;
  total_quotes: number;
  total_pages: number;
  groups: Quote[];
}

export function useQuotes(pageNumber: number = 1) {
  return useQuery({
    queryKey: ["quotes", pageNumber],
    queryFn: () =>
      api.get<QuotesResponse>(`/api/quotes?page_number=${pageNumber}`),
  });
}

export function useQuote(quoteId: string) {
  return useQuery({
    queryKey: ["quotes", quoteId],
    queryFn: () => api.get<Quote>(`/api/quotes/${quoteId}`),
    enabled: !!quoteId,
  });
}
