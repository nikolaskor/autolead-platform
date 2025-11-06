import type { LeadStatus } from "@/types";

interface StatusBadgeProps {
  status: LeadStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const styles = {
    new: "bg-blue-100 text-blue-800 border-blue-200",
    contacted: "bg-yellow-100 text-yellow-800 border-yellow-200",
    qualified: "bg-purple-100 text-purple-800 border-purple-200",
    won: "bg-green-100 text-green-800 border-green-200",
    lost: "bg-gray-100 text-gray-800 border-gray-200",
  };

  const labels = {
    new: "New",
    contacted: "Contacted",
    qualified: "Qualified",
    won: "Won",
    lost: "Lost",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[status]}`}
    >
      {labels[status]}
    </span>
  );
}

