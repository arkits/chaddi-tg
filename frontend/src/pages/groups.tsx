import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable } from "@/components/shared/data-table";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { useGroups, type Group } from "@/hooks/use-groups";
import { formatRelativeTime } from "@/lib/utils";

export default function Groups() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const { data, isLoading } = useGroups(page);

  if (isLoading) {
    return <LoadingState />;
  }

  const columns = [
    {
      key: "name",
      header: "Name",
      render: (g: Group) => g.name ?? "Unknown",
    },
    {
      key: "group_id",
      header: "ID",
      render: (g: Group) => (
        <span className="font-mono text-xs text-muted-foreground">
          {g.group_id}
        </span>
      ),
    },
    {
      key: "updated",
      header: "Last Updated",
      render: (g: Group) => formatRelativeTime(g.updated),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Groups"
        description={`${data?.total_groups ?? 0} total groups`}
      />

      <DataTable
        columns={columns}
        data={data?.groups ?? []}
        keyExtractor={(g) => g.group_id}
        onRowClick={(g) =>
          navigate(`/groups/${g.group_id}`, { viewTransition: true })
        }
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
