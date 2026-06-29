import { useState } from "react";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable } from "@/components/shared/data-table";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { useJobs, type Job } from "@/hooks/use-jobs";
import { formatDate, formatNumber } from "@/lib/utils";

export default function Jobs() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useJobs(page);

  if (isLoading) {
    return <LoadingState />;
  }

  const columns = [
    {
      key: "job_id",
      header: "ID",
      render: (j: Job) => j.job_id,
    },
    {
      key: "from_bakchod",
      header: "Created By",
      render: (j: Job) => j.from_bakchod ?? "-",
    },
    {
      key: "group",
      header: "Group",
      render: (j: Job) => j.group ?? "-",
    },
    {
      key: "created",
      header: "Created",
      render: (j: Job) => formatDate(j.created),
    },
    {
      key: "updated",
      header: "Updated",
      render: (j: Job) => formatDate(j.updated),
    },
    {
      key: "job_context",
      header: "Context",
      render: (j: Job) => (
        <pre className="max-w-xs overflow-auto whitespace-pre-wrap text-xs">
          {JSON.stringify(j.job_context, null, 2)}
        </pre>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Scheduled Jobs"
        description={`${formatNumber(data?.total_jobs ?? 0)} total jobs`}
      />

      <DataTable
        columns={columns}
        data={data?.jobs ?? []}
        keyExtractor={(j) => j.job_id.toString()}
      />

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {data.current_page} of {data.total_pages}
          </span>
          <Button
            variant="outline"
            disabled={page >= data.total_pages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}