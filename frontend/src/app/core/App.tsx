import { Navigate, Route, Routes } from "react-router-dom";

import { AppointmentBookingScreen } from "../features/consultation-records/AppointmentBookingScreen";
import { ConsultationDetailScreen } from "../features/consultation-records/ConsultationDetailScreen";
import { ConsultationRecordsScreen } from "../features/consultation-records/ConsultationRecordsScreen";
import { ConsultationSummaryScreen } from "../features/consultation-records/ConsultationSummaryScreen";
import { NewConsultationScreen } from "../features/consultation-records/NewConsultationScreen";
import { DashboardScreen } from "../features/dashboard/DashboardScreen";
import { AppointmentsScreen } from "../features/appointments/AppointmentsScreen";
import { AppLayout } from "../layout/AppLayout";

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardScreen />} />
        <Route path="appointments" element={<AppointmentsScreen />} />
        <Route path="consultations" element={<ConsultationRecordsScreen />} />
        <Route path="consultations/new" element={<NewConsultationScreen />} />
        <Route path="consultations/:consultationId" element={<ConsultationDetailScreen />} />
        <Route path="consultations/:consultationId/summary" element={<ConsultationSummaryScreen />} />
        <Route
          path="consultations/:consultationId/appointments/new"
          element={<AppointmentBookingScreen />}
        />
      </Route>
    </Routes>
  );
}
