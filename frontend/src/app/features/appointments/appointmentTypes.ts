export interface AppointmentRecommendation {
  id: string;
  treatment: string;
}

export interface AppointmentListItem {
  id: string;
  consultation_id: string;
  patient_name: string;
  recommendation: AppointmentRecommendation;
  scheduled_at: string;
  location: string;
  created_at: string;
}

export interface AppointmentListResponse {
  items: AppointmentListItem[];
}
