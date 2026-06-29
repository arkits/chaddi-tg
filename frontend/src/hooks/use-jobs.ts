import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface Job {
  job_id: number;
  created: string;
  updated: string;
  from_bakchod: string | null;
  group: string | null;
  job_context: Record<string, unknown>;
}

export interface JobsResponse {
  current_page: number;
  total_jobs: number;
  total_pages: number;
  jobs: Job[];
}

export function useJobs(pageNumber: number = 1) {
  return useQuery({
    queryKey: ["jobs", pageNumber],
    queryFn: () => api.get<JobsResponse>(`/api/jobs?page_number=${pageNumber}`),
  });
}
