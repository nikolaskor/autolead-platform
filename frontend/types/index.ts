export type LeadSource = "website" | "email" | "facebook" | "manual";
export type LeadStatus = "new" | "contacted" | "qualified" | "won" | "lost";
export type SenderType = "customer" | "ai" | "human";
export type MessageDirection = "inbound" | "outbound";

export interface Lead {
  id: string;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  vehicle_interest?: string;
  initial_message: string;
  source: LeadSource;
  status: LeadStatus;
  created_at: string;
  last_contact_at?: string;
  dealership_id: string;
  conversation_count?: number;
  source_url?: string;
}

export interface Conversation {
  id: string;
  lead_id: string;
  channel: string;
  direction: MessageDirection;
  sender: string;
  sender_type: SenderType;
  message_content: string;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  limit: number;
}

export interface LeadFilters {
  status?: LeadStatus;
  source?: LeadSource;
  limit?: number;
  offset?: number;
}
