export interface DashboardMetrics {
  total_consultations: number;
  booked_appointments: number;
  conversion_rate: number;
}

export interface DashboardTrend {
  day: string;
  consultation_count: number;
}

export type DashboardActivityType =
  | "conversation_started"
  | "consultation_completed"
  | "appointment_booked";

export interface DashboardActivity {
  activity_type: DashboardActivityType;
  consultation_id: string;
  timestamp: string;
}

export interface DashboardPendingClinicalReview {
  consultation_id: string;
  patient_name: string;
  primary_concern: string;
  recommended_procedure: string;
  status: "PENDING";
}

export interface DashboardResponse extends DashboardMetrics {
  consultation_trends: DashboardTrend[];
  recent_activity: DashboardActivity[];
  pending_clinical_reviews: DashboardPendingClinicalReview[];
}
