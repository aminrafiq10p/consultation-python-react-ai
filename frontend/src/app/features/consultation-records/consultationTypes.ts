export const CONSULTATION_STATUSES = [
  "PENDING",
  "BOOKED",
  "COMPLETED",
] as const;

export type ConsultationStatus = (typeof CONSULTATION_STATUSES)[number];

export interface ConsultationRecord {
  id: string;
  patient_name: string;
  primary_concern: string;
  recommended_procedure: string;
  status: ConsultationStatus;
}

export interface ConsultationListResponse {
  items: ConsultationRecord[];
}

export interface ConsultationListCriteria {
  search?: string;
  status?: ConsultationStatus;
}

export const MESSAGE_ROLES = ["USER", "ASSISTANT"] as const;

export type MessageRole = (typeof MESSAGE_ROLES)[number];

export type StructuredPayloadScalar = string | number | boolean | null;

export type StructuredPayload = Record<
  string,
  StructuredPayloadScalar | StructuredPayloadScalar[]
>;

export interface ConsultationMessage {
  id: string;
  consultation_id: string;
  role: MessageRole;
  content: string;
  structured_payload: StructuredPayload | null;
  created_at: string;
}

export interface ConsultationMessageHistory {
  items: ConsultationMessage[];
}

export interface ConsultationMessageExchange {
  user_message: ConsultationMessage;
  assistant_message: ConsultationMessage;
}
