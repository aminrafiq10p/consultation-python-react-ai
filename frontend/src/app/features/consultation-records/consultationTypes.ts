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
