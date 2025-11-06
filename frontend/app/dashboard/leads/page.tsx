import { Suspense } from "react";
import { fetchLeads } from "@/lib/api";
import { LeadFilters } from "@/components/leads/LeadFilters";
import { LeadsTable } from "@/components/leads/LeadsTable";
import type { LeadStatus, LeadSource } from "@/types";

interface LeadsPageProps {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function LeadsPage({ searchParams }: LeadsPageProps) {
  const params = await searchParams;
  const status = params.status as LeadStatus | undefined;
  const source = params.source as LeadSource | undefined;

  // Fetch leads with filters
  const response = await fetchLeads({
    status,
    source,
    limit: 100, // For now, fetch all leads
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
          <p className="mt-1 text-sm text-gray-500">
            {response.total} {response.total === 1 ? "lead" : "leads"} total
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <Suspense fallback={<div>Loading filters...</div>}>
          <LeadFilters />
        </Suspense>
      </div>

      <Suspense fallback={<div>Loading leads...</div>}>
        <LeadsTable leads={response.items} />
      </Suspense>

      {response.items.length > 0 && (
        <div className="text-sm text-gray-500">
          Showing {response.items.length} of {response.total} leads
        </div>
      )}
    </div>
  );
}

