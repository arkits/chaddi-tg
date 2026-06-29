import { useEffect, useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/shared/page-header";
import { getSocketUrl } from "@/lib/api-client";
import { io, Socket } from "socket.io-client";

interface LogLine {
  id: number;
  text: string;
  timestamp: Date;
}

export default function Logs() {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const socketRef = useRef<Socket | null>(null);
  const logIdRef = useRef(0);

  useEffect(() => {
    const socketUrl = getSocketUrl();
    socketRef.current = io(socketUrl, {
      path: "/socket.io",
      transports: ["websocket", "polling"],
    });

    socketRef.current.on("connect", () => {
      setIsConnected(true);
    });

    socketRef.current.on("disconnect", () => {
      setIsConnected(false);
      setIsStreaming(false);
    });

    socketRef.current.on("log_connected", () => {
      setIsStreaming(true);
    });

    const appendLog = (text: string) => {
      setLogs((prev) => {
        const newLogs = [
          ...prev,
          {
            id: logIdRef.current++,
            text,
            timestamp: new Date(),
          },
        ];
        if (newLogs.length > 500) {
          return newLogs.slice(-500);
        }
        return newLogs;
      });
    };

    socketRef.current.on("log_line", (data: { content: string }) => {
      appendLog(data.content);
    });

    socketRef.current.on("log_error", (data: { message: string }) => {
      console.error("Log error:", data.message);
      appendLog(`[error] ${data.message}`);
      setIsStreaming(false);
    });

    socketRef.current.on("message", (data: { message: Record<string, unknown> }) => {
      appendLog(`[message] ${JSON.stringify(data.message)}`);
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const handleStartStream = () => {
    if (socketRef.current) {
      socketRef.current.emit("start_log_stream");
    }
  };

  const handleStopStream = () => {
    if (socketRef.current) {
      socketRef.current.emit("stop_log_stream");
      setIsStreaming(false);
    }
  };

  const handleClear = () => {
    setLogs([]);
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Logs" description="Real-time log streaming">
        <div className="flex items-center gap-2">
          <div
            className={`h-2 w-2 rounded-full ${
              isConnected ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span className="text-sm text-muted-foreground">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </PageHeader>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Log Stream</CardTitle>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleClear}
            >
              Clear
            </Button>
            {isStreaming ? (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleStopStream}
              >
                Stop Stream
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={handleStartStream}
                disabled={!isConnected}
              >
                Start Stream
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div
            ref={logContainerRef}
            className="scrollbar-theme h-96 overflow-auto rounded-xl border border-emerald-400/30 bg-[linear-gradient(160deg,hsl(190_52%_8%),hsl(205_64%_6%))] p-4 font-mono text-sm text-emerald-200"
          >
            {logs.length === 0 ? (
              <p className="text-emerald-100/70">
                {isStreaming
                  ? "Waiting for logs..."
                  : "Click 'Start Stream' to begin receiving logs"}
              </p>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="whitespace-pre-wrap">
                  {log.text}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
