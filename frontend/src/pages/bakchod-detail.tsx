import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { MetadataEditor } from "@/components/shared/metadata-editor";
import {
  useBakchod,
  useBakchodGroups,
  useSetBakchodMetadata,
  useSetBakchodRokda,
} from "@/hooks/use-bakchods";
import { formatNumber, formatDate } from "@/lib/utils";
import { useState } from "react";
import { ArrowLeft } from "lucide-react";

export default function BakchodDetail() {
  const { tgId } = useParams<{ tgId: string }>();
  const navigate = useNavigate();
  const { data: bakchod, isLoading } = useBakchod(tgId!);
  const { data: groups } = useBakchodGroups(tgId!);
  const setRokda = useSetBakchodRokda();
  const setMetadata = useSetBakchodMetadata();

  const [rokdaValue, setRokdaValue] = useState("");

  if (isLoading) {
    return <LoadingState />;
  }

  if (!bakchod) {
    return (
      <div className="space-y-6">
        <Button
          variant="ghost"
          onClick={() => navigate("/bakchods", { viewTransition: true })}
        >
          <ArrowLeft className="mr-2 h-4 w-4" /> Back
        </Button>
        <p>Bakchod not found</p>
      </div>
    );
  }

  const handleSetRokda = () => {
    if (rokdaValue && tgId) {
      setRokda.mutate({ bakchodId: tgId, rokda: rokdaValue });
      setRokdaValue("");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={bakchod.pretty_name ?? bakchod.username ?? "Unknown"}
        description={`TG ID: ${bakchod.tg_id}`}
      >
        <Button
          variant="ghost"
          onClick={() => navigate("/bakchods", { viewTransition: true })}
        >
          <ArrowLeft className="mr-2 h-4 w-4" /> Back
        </Button>
      </PageHeader>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>User Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Username</span>
              <span>{bakchod.username ? `@${bakchod.username}` : "-"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Pretty Name</span>
              <span>{bakchod.pretty_name ?? "-"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Rokda</span>
              <span>{formatNumber(Math.floor(bakchod.rokda))}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Created</span>
              <span>{bakchod.created ? formatDate(bakchod.created) : "-"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Last Seen</span>
              <span>{bakchod.lastseen ? formatDate(bakchod.lastseen) : "Never"}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Set Rokda</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                type="number"
                placeholder="New rokda value"
                value={rokdaValue}
                onChange={(e) => setRokdaValue(e.target.value)}
              />
              <Button onClick={handleSetRokda} disabled={setRokda.isPending}>
                Update
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Groups ({groups?.length ?? 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {groups && groups.length > 0 ? (
            <div className="space-y-2">
              {groups.map((group) => (
                <div
                  key={group.group_id}
                  className="flex cursor-pointer items-center justify-between rounded-md border p-2 hover:bg-muted"
                  onClick={() =>
                    navigate(`/groups/${group.group_id}`, { viewTransition: true })
                  }
                >
                  <span>{group.name}</span>
                  <span className="text-sm text-muted-foreground">
                    {formatDate(group.updated)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No groups found</p>
          )}
        </CardContent>
      </Card>

      <MetadataEditor
        metadata={bakchod.metadata}
        isPending={setMetadata.isPending}
        onSave={(metadataJson) => {
          if (tgId) {
            setMetadata.mutate({ bakchodId: tgId, metadata: metadataJson });
          }
        }}
      />
    </div>
  );
}
