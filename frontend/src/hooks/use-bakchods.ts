import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface Bakchod {
  tg_id: string;
  username: string | null;
  pretty_name: string | null;
  rokda: number;
  lastseen: string | null;
  created: string | null;
  updated: string | null;
  metadata: Record<string, unknown>;
}

export interface BakchodsResponse {
  current_page: number;
  total_bakchods: number;
  total_pages: number;
  bakchods: Bakchod[];
}

export interface BakchodGroup {
  group_id: string;
  name: string;
  created: string;
  updated: string;
}

export function useBakchods(pageNumber: number = 1) {
  return useQuery({
    queryKey: ["bakchods", pageNumber],
    queryFn: () =>
      api.get<BakchodsResponse>(`/api/bakchods?page_number=${pageNumber}`),
  });
}

export function useBakchod(tgId: string) {
  return useQuery({
    queryKey: ["bakchods", tgId],
    queryFn: () => api.get<Bakchod>(`/api/bakchods/${tgId}`),
    enabled: !!tgId,
  });
}

export function useBakchodGroups(tgId: string) {
  return useQuery({
    queryKey: ["bakchods", tgId, "groups"],
    queryFn: () => api.get<BakchodGroup[]>(`/api/bakchods/${tgId}/groups`),
    enabled: !!tgId,
  });
}

export function useSetBakchodRokda() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      bakchodId,
      rokda,
    }: {
      bakchodId: string;
      rokda: string;
    }) =>
      api.post("/api/bakchod/rokda", {
        bakchod_id: bakchodId,
        rokda,
      }),
    onSuccess: (_, { bakchodId }) => {
      queryClient.invalidateQueries({ queryKey: ["bakchods", bakchodId] });
    },
  });
}

export function useSetBakchodMetadata() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      bakchodId,
      metadata,
    }: {
      bakchodId: string;
      metadata: string;
    }) =>
      api.post("/api/bakchod/metadata", {
        bakchod_id: bakchodId,
        metadata,
      }),
    onSuccess: (_, { bakchodId }) => {
      queryClient.invalidateQueries({ queryKey: ["bakchods", bakchodId] });
    },
  });
}
