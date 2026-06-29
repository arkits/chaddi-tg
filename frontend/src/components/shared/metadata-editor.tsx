import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface MetadataEditorProps {
  metadata: Record<string, unknown>;
  onSave: (metadataJson: string) => void;
  isPending?: boolean;
}

export function MetadataEditor({
  metadata,
  onSave,
  isPending,
}: MetadataEditorProps) {
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setText(JSON.stringify(metadata, null, 2));
    setError(null);
  }, [metadata]);

  const handleSave = () => {
    try {
      JSON.parse(text);
      setError(null);
      onSave(text);
    } catch {
      setError("Invalid JSON — fix syntax before saving.");
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Metadata</CardTitle>
        <Button size="sm" onClick={handleSave} disabled={isPending}>
          {isPending ? "Saving..." : "Save"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-2">
        <textarea
          className="min-h-48 w-full rounded-xl border border-input bg-muted p-4 font-mono text-sm focus-visible:border-primary/65 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/35"
          value={text}
          onChange={(e) => setText(e.target.value)}
          spellCheck={false}
        />
        {error && <p className="text-sm text-destructive">{error}</p>}
      </CardContent>
    </Card>
  );
}
