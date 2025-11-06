"use client";

import { useRouter, useSearchParams } from "next/navigation";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import type { LeadStatus, LeadSource } from "@/types";

export function LeadFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const currentStatus = searchParams.get("status") as LeadStatus | null;
  const currentSource = searchParams.get("source") as LeadSource | null;

  const updateFilter = (key: string, value: string | null) => {
    const params = new URLSearchParams(searchParams.toString());

    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }

    router.push(`/dashboard/leads?${params.toString()}`);
  };

  const statusOptions: { value: LeadStatus | null; label: string }[] = [
    { value: null, label: "All Statuses" },
    { value: "new", label: "New" },
    { value: "contacted", label: "Contacted" },
    { value: "qualified", label: "Qualified" },
    { value: "won", label: "Won" },
    { value: "lost", label: "Lost" },
  ];

  const sourceOptions: { value: LeadSource | null; label: string }[] = [
    { value: null, label: "All Sources" },
    { value: "website", label: "Website" },
    { value: "email", label: "Email" },
    { value: "facebook", label: "Facebook" },
    { value: "manual", label: "Manual" },
  ];

  return (
    <div className="flex gap-3">
      {/* Status Filter */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="w-[180px] justify-between">
            {currentStatus
              ? statusOptions.find((o) => o.value === currentStatus)?.label
              : "All Statuses"}
            <svg
              className="ml-2 h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-[180px]">
          {statusOptions.map((option) => (
            <DropdownMenuItem
              key={option.value || "all"}
              onClick={() => updateFilter("status", option.value)}
            >
              {option.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Source Filter */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="w-[180px] justify-between">
            {currentSource
              ? sourceOptions.find((o) => o.value === currentSource)?.label
              : "All Sources"}
            <svg
              className="ml-2 h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-[180px]">
          {sourceOptions.map((option) => (
            <DropdownMenuItem
              key={option.value || "all"}
              onClick={() => updateFilter("source", option.value)}
            >
              {option.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

