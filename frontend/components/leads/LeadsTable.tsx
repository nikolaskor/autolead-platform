"use client";

import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusBadge } from "./StatusBadge";
import { SourceBadge } from "./SourceBadge";
import type { Lead } from "@/types";

interface LeadsTableProps {
  leads: Lead[];
}

export function LeadsTable({ leads }: LeadsTableProps) {
  if (leads.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-300 bg-white p-12 text-center">
        <svg
          className="h-12 w-12 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
          />
        </svg>
        <h3 className="mt-4 text-lg font-semibold text-gray-900">No leads found</h3>
        <p className="mt-2 text-sm text-gray-500">
          No leads match your current filters.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-white">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Customer</TableHead>
            <TableHead>Vehicle Interest</TableHead>
            <TableHead>Source</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Created</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {leads.map((lead) => (
            <TableRow
              key={lead.id}
              className="cursor-pointer hover:bg-gray-50"
            >
              <TableCell>
                <Link href={`/dashboard/leads/${lead.id}`} className="block">
                  <div className="font-medium text-gray-900">
                    {lead.customer_name}
                  </div>
                  <div className="text-sm text-gray-500">
                    {lead.customer_email}
                  </div>
                </Link>
              </TableCell>
              <TableCell>
                <Link href={`/dashboard/leads/${lead.id}`} className="block">
                  {lead.vehicle_interest || (
                    <span className="text-gray-400">Not specified</span>
                  )}
                </Link>
              </TableCell>
              <TableCell>
                <Link href={`/dashboard/leads/${lead.id}`} className="block">
                  <SourceBadge source={lead.source} />
                </Link>
              </TableCell>
              <TableCell>
                <Link href={`/dashboard/leads/${lead.id}`} className="block">
                  <StatusBadge status={lead.status} />
                </Link>
              </TableCell>
              <TableCell>
                <Link href={`/dashboard/leads/${lead.id}`} className="block">
                  <div className="text-sm text-gray-900">
                    {formatDistanceToNow(new Date(lead.created_at), {
                      addSuffix: true,
                    })}
                  </div>
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

