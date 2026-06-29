import { useState } from "react";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingState } from "@/components/shared/loading-state";
import { useQuotes, type Quote } from "@/hooks/use-quotes";
import { formatDate } from "@/lib/utils";

export default function Quotes() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuotes(page);

  if (isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Quotes"
        description={`${data?.total_quotes ?? 0} total quotes`}
      />

      <div className="grid gap-4">
        {data?.groups?.map((quote: Quote) => (
          <Card key={quote.quote_id}>
            <CardContent className="p-4">
              <p className="text-lg italic mb-2">"{quote.text}"</p>
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>- {quote.author_bakchod}</span>
                <span>in {quote.quoted_in_group}</span>
              </div>
              <div className="text-xs text-muted-foreground mt-2">
                {formatDate(quote.created)}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

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