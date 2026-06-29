import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface DashboardMetrics {
  bakchods_count: number;
  groups_count: number;
  messages_count: number;
  quotes_count: number;
  roll_count: number;
  jobs_count: number;
  recent_messages: number;
  recent_bakchods: number;
}

export interface DashboardActivity {
  most_active_bakchod: {
    pretty_name: string | null;
    username: string | null;
  } | null;
  most_active_group: {
    name: string | null;
  } | null;
  latest_message_time: string | null;
}

export interface DashboardRandomQuote {
  quote: {
    text: string;
    created: string;
    author_bakchod: {
      pretty_name: string;
      username: string;
    };
    quoted_in_group: {
      name: string;
    };
  } | null;
}

export interface DashboardVersion {
  semver: string;
  git_commit_id: string;
  git_commit_time: string;
  pretty_uptime: string;
}

export function useDashboardMetrics() {
  return useQuery({
    queryKey: ["dashboard", "metrics"],
    queryFn: () => api.get<DashboardMetrics>("/api/dashboard/metrics"),
  });
}

export function useDashboardActivity() {
  return useQuery({
    queryKey: ["dashboard", "activity"],
    queryFn: () => api.get<DashboardActivity>("/api/dashboard/activity"),
  });
}

export function useDashboardRandomQuote() {
  return useQuery({
    queryKey: ["dashboard", "random-quote"],
    queryFn: () => api.get<DashboardRandomQuote>("/api/dashboard/random-quote"),
  });
}

export function useDashboardVersion() {
  return useQuery({
    queryKey: ["dashboard", "version"],
    queryFn: () => api.get<DashboardVersion>("/api/dashboard/version"),
  });
}
