import { format } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Lead } from "@/types";

interface LeadInfoSectionProps {
  lead: Lead;
}

export function LeadInfoSection({ lead }: LeadInfoSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Lead Information</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <p className="text-sm font-medium text-gray-500">Lead ID</p>
          <p className="mt-1 font-mono text-sm text-gray-900">{lead.id}</p>
        </div>

        <div>
          <p className="text-sm font-medium text-gray-500">Created</p>
          <p className="mt-1 text-sm text-gray-900">
            {format(new Date(lead.created_at), "PPPP 'at' p")}
          </p>
        </div>

        {lead.source_url && (
          <div>
            <p className="text-sm font-medium text-gray-500">Source URL</p>
            <a
              href={lead.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-1 block truncate text-sm text-blue-600 hover:text-blue-800"
            >
              {lead.source_url}
            </a>
          </div>
        )}

        {lead.last_contact_at && (
          <div>
            <p className="text-sm font-medium text-gray-500">Last Contact</p>
            <p className="mt-1 text-sm text-gray-900">
              {format(new Date(lead.last_contact_at), "PPPP 'at' p")}
            </p>
          </div>
        )}

        <div>
          <p className="text-sm font-medium text-gray-500">Initial Message</p>
          <p className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
            {lead.initial_message}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

