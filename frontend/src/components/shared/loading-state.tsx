import { Skeleton } from "@/components/ui/skeleton";

export function LoadingState() {
  return (
    <div className="animate-rise space-y-5">
      <Skeleton className="h-10 w-56 rounded-xl" />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Skeleton className="h-32 rounded-2xl" />
        <Skeleton className="h-32 rounded-2xl" />
        <Skeleton className="h-32 rounded-2xl" />
        <Skeleton className="h-32 rounded-2xl" />
      </div>
      <Skeleton className="h-72 rounded-2xl" />
    </div>
  );
}
