import { auth } from "@clerk/nextjs/server";
import type { Lead, Conversation, LeadFilters, PaginatedResponse } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Get authentication token for API requests
 * This is used in Server Components
 */
export async function getAuthToken(): Promise<string | null> {
  const { getToken } = await auth();
  return await getToken();
}

/**
 * Make an authenticated API request
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: "An error occurred",
    }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Fetch leads with optional filters
 */
export async function fetchLeads(
  filters: LeadFilters = {}
): Promise<PaginatedResponse<Lead>> {
  const params = new URLSearchParams();

  if (filters.status) params.append("status", filters.status);
  if (filters.source) params.append("source", filters.source);
  if (filters.limit) params.append("limit", filters.limit.toString());
  if (filters.offset) params.append("offset", filters.offset.toString());

  const queryString = params.toString();
  const endpoint = `/api/v1/leads${queryString ? `?${queryString}` : ""}`;

  return apiRequest<PaginatedResponse<Lead>>(endpoint);
}

/**
 * Fetch a single lead by ID
 */
export async function fetchLead(id: string): Promise<Lead> {
  return apiRequest<Lead>(`/api/v1/leads/${id}`);
}

/**
 * Fetch conversations for a lead
 */
export async function fetchConversations(
  leadId: string
): Promise<Conversation[]> {
  return apiRequest<Conversation[]>(`/api/v1/leads/${leadId}/conversations`);
}

/**
 * Update a lead
 */
export async function updateLead(
  id: string,
  data: Partial<Lead>
): Promise<Lead> {
  return apiRequest<Lead>(`/api/v1/leads/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/**
 * Create a new conversation
 */
export async function createConversation(data: {
  lead_id: string;
  message_content: string;
  channel: string;
}): Promise<Conversation> {
  return apiRequest<Conversation>("/api/v1/conversations", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
