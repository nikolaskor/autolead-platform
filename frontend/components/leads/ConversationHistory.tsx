import { format } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Conversation } from "@/types";

interface ConversationHistoryProps {
  conversations: Conversation[];
}

export function ConversationHistory({
  conversations,
}: ConversationHistoryProps) {
  if (conversations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Conversation History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center">
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
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <p className="mt-4 text-sm text-gray-500">No conversations yet</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Conversation History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {conversations.map((conversation) => {
            const isCustomer = conversation.sender_type === "customer";
            const isAI = conversation.sender_type === "ai";
            const isHuman = conversation.sender_type === "human";

            return (
              <div
                key={conversation.id}
                className={`flex ${
                  isCustomer ? "justify-start" : "justify-end"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-3 ${
                    isCustomer
                      ? "bg-blue-50 text-blue-900"
                      : isAI
                      ? "bg-gray-100 text-gray-900"
                      : "bg-green-50 text-green-900"
                  }`}
                >
                  <div className="mb-2 flex items-center gap-2">
                    {isAI && (
                      <svg
                        className="h-4 w-4 text-gray-600"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                        />
                      </svg>
                    )}
                    <span className="text-xs font-semibold">
                      {conversation.sender}
                    </span>
                    <span className="text-xs text-gray-500">
                      {format(new Date(conversation.created_at), "MMM d, HH:mm")}
                    </span>
                  </div>
                  <p className="text-sm whitespace-pre-wrap">
                    {conversation.message_content}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

