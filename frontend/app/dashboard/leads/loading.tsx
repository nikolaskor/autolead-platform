export default function LeadsLoading() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-8 w-32 animate-pulse rounded bg-gray-200"></div>
          <div className="mt-2 h-4 w-24 animate-pulse rounded bg-gray-200"></div>
        </div>
      </div>

      <div className="flex gap-3">
        <div className="h-10 w-[180px] animate-pulse rounded bg-gray-200"></div>
        <div className="h-10 w-[180px] animate-pulse rounded bg-gray-200"></div>
      </div>

      <div className="rounded-lg border bg-white">
        <div className="divide-y">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="p-4">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <div className="h-4 w-32 animate-pulse rounded bg-gray-200"></div>
                  <div className="h-3 w-48 animate-pulse rounded bg-gray-200"></div>
                </div>
                <div className="h-6 w-20 animate-pulse rounded-full bg-gray-200"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

