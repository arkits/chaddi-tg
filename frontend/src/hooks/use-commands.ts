import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface CommandStats {
  total: number;
  last_24h: number;
  last_7d: number;
}

export interface TopCommand {
  command_name: string;
  count: number;
}

export interface CommandByGroup {
  name: string;
  count: number;
}

export interface CommandByUser {
  pretty_name: string;
  username: string;
  count: number;
}

export interface HourlyData {
  hour: string;
  count: number;
}

export interface RecentCommand {
  id: number;
  command_name: string;
  executed_at: string;
  from_bakchod: string | null;
  group: string | null;
}

export function useCommandStats() {
  return useQuery({
    queryKey: ["commands", "stats"],
    queryFn: () => api.get<CommandStats>("/api/commands/stats"),
  });
}

export function useTopCommands(limit: number = 10) {
  return useQuery({
    queryKey: ["commands", "top", limit],
    queryFn: () => api.get<TopCommand[]>(`/api/commands/top?limit=${limit}`),
  });
}

export function useCommandsByGroup(limit: number = 10) {
  return useQuery({
    queryKey: ["commands", "by-group", limit],
    queryFn: () =>
      api.get<CommandByGroup[]>(`/api/commands/by-group?limit=${limit}`),
  });
}

export function useCommandsByUser(limit: number = 10) {
  return useQuery({
    queryKey: ["commands", "by-user", limit],
    queryFn: () =>
      api.get<CommandByUser[]>(`/api/commands/by-user?limit=${limit}`),
  });
}

export function useCommandsHourly() {
  return useQuery({
    queryKey: ["commands", "hourly"],
    queryFn: () => api.get<HourlyData[]>("/api/commands/hourly"),
  });
}

export function useCommandsRecent(limit: number = 50) {
  return useQuery({
    queryKey: ["commands", "recent", limit],
    queryFn: () =>
      api.get<RecentCommand[]>(`/api/commands/recent?limit=${limit}`),
  });
}
