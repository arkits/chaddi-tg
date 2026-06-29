import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable } from "@/components/shared/data-table";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { useBakchods, type Bakchod } from "@/hooks/use-bakchods";
import { formatRelativeTime, formatNumber } from "@/lib/utils";

export default function Bakchods() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const { data, isLoading } = useBakchods(page);

  if (isLoading) {
    return <LoadingState />;
  }

  const columns = [
    {
      key: "pretty_name",
      header: "Name",
      render: (b: Bakchod) => b.pretty_name ?? b.username ?? "Unknown",
    },
    {
      key: "username",
      header: "Username",
      render: (b: Bakchod) => (b.username ? `@${b.username}` : "-"),
    },
    {
      key: "rokda",
      header: "Rokda",
      render: (b: Bakchod) => formatNumber(Math.floor(b.rokda)),
    },
    {
      key: "lastseen",
      header: "Last Seen",
      render: (b: Bakchod) =>
        b.lastseen ? formatRelativeTime(b.lastseen) : "Never",
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Bakchods"
        description={`${data?.total_bakchods ?? 0} total users`}
      />

      <DataTable
        columns={columns}
        data={data?.bakchods ?? []}
        keyExtractor={(b) => b.tg_id}
        onRowClick={(b) =>
          navigate(`/bakchods/${b.tg_id}`, { viewTransition: true })
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
