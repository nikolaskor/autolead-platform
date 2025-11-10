import { format } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "./StatusBadge";
import { SourceBadge } from "./SourceBadge";
import type { Lead } from "@/types";

interface CustomerProfileCardProps {
  lead: Lead;
}

export function CustomerProfileCard({ lead }: CustomerProfileCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Customer Profile</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {lead.customer_name}
          </h2>
        </div>

        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <svg
              className="mt-0.5 h-5 w-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            <div>
              <p className="text-sm font-medium text-gray-500">Email</p>
              <a
                href={`mailto:${lead.customer_email}`}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                {lead.customer_email}
              </a>
            </div>
          </div>

          {lead.customer_phone && (
            <div className="flex items-start gap-3">
              <svg
                className="mt-0.5 h-5 w-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                />
              </svg>
              <div>
                <p className="text-sm font-medium text-gray-500">Phone</p>
                <a
                  href={`tel:${lead.customer_phone}`}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  {lead.customer_phone}
                </a>
              </div>
            </div>
          )}

          {lead.vehicle_interest && (
            <div className="flex items-start gap-3">
              <svg
                className="mt-0.5 h-5 w-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <div>
                <p className="text-sm font-medium text-gray-500">
                  Vehicle Interest
                </p>
                <p className="text-sm text-gray-900">{lead.vehicle_interest}</p>
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-2 pt-2">
          <SourceBadge source={lead.source} />
          <StatusBadge status={lead.status} />
        </div>

        <div className="border-t pt-4">
          <p className="text-xs text-gray-500">
            Created {format(new Date(lead.created_at), "PPp")}
          </p>
          {lead.last_contact_at && (
            <p className="text-xs text-gray-500">
              Last contact {format(new Date(lead.last_contact_at), "PPp")}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

