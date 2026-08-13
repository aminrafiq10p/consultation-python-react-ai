import { Alert, Box, CircularProgress, FormControl, InputLabel, MenuItem, Select, TextField, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { consultationApi } from "./consultationApi";
import { ConsultationRecordsTable } from "./ConsultationRecordsTable";
import { CONSULTATION_STATUSES, type ConsultationListCriteria, type ConsultationRecord, type ConsultationStatus } from "./consultationTypes";

export interface ConsultationListService {
  list: (criteria?: ConsultationListCriteria) => Promise<{ items: ConsultationRecord[] }>;
}

interface ConsultationRecordsScreenProps {
  service?: ConsultationListService;
}

export function ConsultationRecordsScreen({ service = consultationApi }: ConsultationRecordsScreenProps) {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<ConsultationStatus | "">("");
  const [records, setRecords] = useState<ConsultationRecord[]>([]);
  const [state, setState] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    let active = true;
    service.list({ search, status: status || undefined }).then(
      ({ items }) => {
        if (active) {
          setRecords(items);
          setState("success");
        }
      },
      () => {
        if (active) setState("error");
      },
    );
    return () => {
      active = false;
    };
  }, [search, service, status]);

  return (
    <Box>
      <Typography component="h1" variant="h4" gutterBottom>Consultation Records</Typography>
      <Box sx={{ display: "flex", gap: 2, mb: 3, flexWrap: "wrap" }}>
        <TextField label="Search consultations" value={search} onChange={(event) => { setState("loading"); setSearch(event.target.value); }} />
        <FormControl sx={{ minWidth: 190 }}>
          <InputLabel id="status-filter-label">Status</InputLabel>
          <Select labelId="status-filter-label" label="Status" value={status} onChange={(event) => { setState("loading"); setStatus(event.target.value as ConsultationStatus | ""); }}>
            <MenuItem value="">All statuses</MenuItem>
            {CONSULTATION_STATUSES.map((option) => <MenuItem key={option} value={option}>{option}</MenuItem>)}
          </Select>
        </FormControl>
      </Box>

      {state === "loading" && <Box role="status" sx={{ display: "flex", gap: 2, alignItems: "center" }}><CircularProgress size={24} /><span>Loading consultation records…</span></Box>}
      {state === "error" && <Alert severity="error">Consultation records could not be loaded. Please try again.</Alert>}
      {state === "success" && records.length === 0 && <Alert severity="info">No consultation records match your criteria.</Alert>}
      {state === "success" && records.length > 0 && <ConsultationRecordsTable records={records} onSelect={(id) => navigate(`/consultations/${id}`)} />}
    </Box>
  );
}
