import Link from "next/link";
import { fetchLead, fetchConversations } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { CustomerProfileCard } from "@/components/leads/CustomerProfileCard";
import { ConversationHistory } from "@/components/leads/ConversationHistory";
import { LeadInfoSection } from "@/components/leads/LeadInfoSection";

interface LeadDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function LeadDetailPage({ params }: LeadDetailPageProps) {
  const { id } = await params;

  // Fetch lead and conversations in parallel
  const [lead, conversations] = await Promise.all([
    fetchLead(id),
    fetchConversations(id),
  ]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/leads">
            <Button variant="outline" size="sm">
              <svg
                className="mr-2 h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              Back to Leads
            </Button>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Lead Details</h1>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column - Customer profile and info */}
        <div className="space-y-6 lg:col-span-1">
          <CustomerProfileCard lead={lead} />
          <LeadInfoSection lead={lead} />
        </div>

        {/* Right column - Conversation history */}
        <div className="lg:col-span-2">
          <ConversationHistory conversations={conversations} />
        </div>
      </div>
    </div>
  );
}

