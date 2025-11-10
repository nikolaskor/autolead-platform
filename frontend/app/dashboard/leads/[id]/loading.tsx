export default function LeadDetailLoading() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div className="h-9 w-32 animate-pulse rounded bg-gray-200"></div>
        <div className="h-8 w-48 animate-pulse rounded bg-gray-200"></div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column skeleton */}
        <div className="space-y-6 lg:col-span-1">
          <div className="rounded-lg border bg-white p-6">
            <div className="space-y-4">
              <div className="h-8 w-48 animate-pulse rounded bg-gray-200"></div>
              <div className="space-y-3">
                <div className="h-4 w-full animate-pulse rounded bg-gray-200"></div>
                <div className="h-4 w-3/4 animate-pulse rounded bg-gray-200"></div>
                <div className="h-4 w-2/3 animate-pulse rounded bg-gray-200"></div>
              </div>
            </div>
          </div>

          <div className="rounded-lg border bg-white p-6">
            <div className="space-y-3">
              <div className="h-4 w-full animate-pulse rounded bg-gray-200"></div>
              <div className="h-4 w-5/6 animate-pulse rounded bg-gray-200"></div>
            </div>
          </div>
        </div>

        {/* Right column skeleton */}
        <div className="lg:col-span-2">
          <div className="rounded-lg border bg-white p-6">
            <div className="space-y-4">
              <div className="h-6 w-48 animate-pulse rounded bg-gray-200"></div>
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-24 w-full animate-pulse rounded bg-gray-200"
                  ></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

