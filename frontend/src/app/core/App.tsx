import { Navigate, Route, Routes } from "react-router-dom";

import { ConsultationDetailScreen } from "../features/consultation-records/ConsultationDetailScreen";
import { ConsultationRecordsScreen } from "../features/consultation-records/ConsultationRecordsScreen";
import { AppLayout } from "../layout/AppLayout";

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/consultations" replace />} />
        <Route path="consultations" element={<ConsultationRecordsScreen />} />
        <Route path="consultations/:consultationId" element={<ConsultationDetailScreen />} />
      </Route>
    </Routes>
  );
}
