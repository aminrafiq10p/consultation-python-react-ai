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

export interface ConsultationCreationRequest {
  patient_name: string;
  primary_concern: string;
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
  handoff?: BookingHandoff | null;
  created_at: string;
}

export const BOOKING_HANDOFF_ACTIONS = [
  "CONTINUE_CONSULTATION",
  "GENERATE_SUMMARY",
  "VIEW_SUMMARY",
  "VIEW_APPOINTMENTS",
] as const;

export type BookingHandoffAction = (typeof BOOKING_HANDOFF_ACTIONS)[number];

export interface BookingHandoff {
  type: "BOOKING_HANDOFF";
  action: BookingHandoffAction;
  consultation_id: string;
  target: string;
}

export interface ConsultationMessageHistory {
  items: ConsultationMessage[];
}

export interface ConsultationMessageExchange {
  user_message: ConsultationMessage;
  assistant_message: ConsultationMessage;
}

export interface Recommendation {
  id: string;
  treatment: string;
  position: number;
}

export interface ConsultationSummary {
  id: string;
  consultation_id: string;
  patient_summary: string;
  recommended_treatments: Recommendation[];
  recommendation_rationale: string | null;
  created_at: string;
}

export interface AppointmentBookingRequest {
  recommendation_id: string;
  scheduled_at: string;
  location: string;
}

export interface AppointmentRecommendation {
  id: string;
  treatment: string;
}

export interface Appointment {
  id: string;
  consultation_id: string;
  recommendation: AppointmentRecommendation;
  scheduled_at: string;
  location: string;
  created_at: string;
}
