import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { useSetGroupMetadata } from "@/hooks/use-groups";

function getEnabledCommands(metadata: Record<string, unknown>): string[] {
  const commands = metadata.enabled_commands;
  if (!Array.isArray(commands)) {
    return [];
  }
  return commands.filter((command): command is string => typeof command === "string");
}

interface GroupCommandSettingsProps {
  groupId: string;
  metadata: Record<string, unknown>;
}

export function GroupCommandSettings({
  groupId,
  metadata,
}: GroupCommandSettingsProps) {
  const setMetadata = useSetGroupMetadata();
  const enabledCommands = getEnabledCommands(metadata);
  const goodMorningEnabled = Boolean(metadata.good_morning_enabled);

  const saveMetadata = (next: Record<string, unknown>) => {
    setMetadata.mutate({
      groupId,
      metadata: JSON.stringify(next),
    });
  };

  const toggleCommand = (command: string, enabled: boolean) => {
    const commands = [...getEnabledCommands(metadata)];
    const nextCommands = enabled
      ? commands.includes(command)
        ? commands
        : [...commands, command]
      : commands.filter((item) => item !== command);

    saveMetadata({ ...metadata, enabled_commands: nextCommands });
  };

  const toggleGoodMorning = (enabled: boolean) => {
    saveMetadata({ ...metadata, good_morning_enabled: enabled });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Command Settings</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <label htmlFor="toggle-ask" className="text-sm">
            Enable /ask command
          </label>
          <Switch
            id="toggle-ask"
            checked={enabledCommands.includes("ask")}
            disabled={setMetadata.isPending}
            onCheckedChange={(checked) => toggleCommand("ask", checked)}
          />
        </div>
        <div className="flex items-center justify-between gap-4">
          <label htmlFor="toggle-ai" className="text-sm">
            Enable /ai command
          </label>
          <Switch
            id="toggle-ai"
            checked={enabledCommands.includes("ai")}
            disabled={setMetadata.isPending}
            onCheckedChange={(checked) => toggleCommand("ai", checked)}
          />
        </div>
        <div className="flex items-center justify-between gap-4">
          <label htmlFor="toggle-gm" className="text-sm">
            Enable Good Morning Greeting
          </label>
          <Switch
            id="toggle-gm"
            checked={goodMorningEnabled}
            disabled={setMetadata.isPending}
            onCheckedChange={toggleGoodMorning}
          />
        </div>
      </CardContent>
    </Card>
  );
}
