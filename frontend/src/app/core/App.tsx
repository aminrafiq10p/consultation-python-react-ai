import { Navigate, Route, Routes } from "react-router-dom";

import { AppointmentBookingScreen } from "../features/consultation-records/AppointmentBookingScreen";
import { ConsultationDetailScreen } from "../features/consultation-records/ConsultationDetailScreen";
import { ConsultationRecordsScreen } from "../features/consultation-records/ConsultationRecordsScreen";
import { ConsultationSummaryScreen } from "../features/consultation-records/ConsultationSummaryScreen";
import { AppLayout } from "../layout/AppLayout";

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/consultations" replace />} />
        <Route path="consultations" element={<ConsultationRecordsScreen />} />
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
