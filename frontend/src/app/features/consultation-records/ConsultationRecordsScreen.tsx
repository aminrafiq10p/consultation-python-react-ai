import { Alert, Box, Button, CircularProgress, Stack, TextField, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { consultationApi } from "./consultationApi";
import { ConsultationRecordsTable } from "./ConsultationRecordsTable";
import { CONSULTATION_STATUSES, type ConsultationListCriteria, type ConsultationRecord, type ConsultationStatus } from "./consultationTypes";
import { PageHeader } from "../../ui/visualSystem";

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
    <Box sx={{ minWidth: 0 }}>
      <PageHeader
        title="Consultation Records"
        subtitle="Review and manage historical patient consultations and AI-assisted procedure recommendations."
      >
        <TextField
          label="Search consultations"
          placeholder="Search patient or ID..."
          value={search}
          onChange={(event) => { setState("loading"); setSearch(event.target.value); }}
          sx={{ width: { xs: "100%", sm: 260 }, flexShrink: 0 }}
        />
      </PageHeader>

      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={{ xs: 1, sm: 1.25 }}
        sx={{ mb: 2.25, alignItems: { xs: "stretch", sm: "center" } }}
      >
        <Typography variant="caption" sx={{ fontWeight: 800, letterSpacing: "0.08em", color: "text.secondary", mr: { sm: 0.5 } }}>
          FILTER BY STATUS
        </Typography>
        <Stack direction="row" spacing={1} useFlexGap role="group" aria-label="Filter by status" sx={{ flexWrap: "wrap" }}>
          <StatusFilterButton label="All" selected={status === ""} onClick={() => { setState("loading"); setStatus(""); }} />
          {CONSULTATION_STATUSES.map((option) => (
            <StatusFilterButton key={option} label={option} selected={status === option} onClick={() => { setState("loading"); setStatus(option); }} />
          ))}
        </Stack>
      </Stack>

      {state === "loading" && <Box role="status" sx={{ display: "flex", gap: 2, alignItems: "center" }}><CircularProgress size={24} /><span>Loading consultation records…</span></Box>}
      {state === "error" && <Alert severity="error">Consultation records could not be loaded. Please try again.</Alert>}
      {state === "success" && records.length === 0 && <Alert severity="info">No consultation records match your criteria.</Alert>}
      {state === "success" && records.length > 0 && <ConsultationRecordsTable records={records} onSelect={(id) => navigate(`/consultations/${id}`)} />}
    </Box>
  );
}

function StatusFilterButton({ label, selected, onClick }: { label: string; selected: boolean; onClick: () => void }) {
  return (
    <Button
      type="button"
      size="small"
      variant={selected ? "contained" : "outlined"}
      aria-pressed={selected}
      onClick={onClick}
      sx={{ minHeight: 34, px: 2, borderRadius: 999, bgcolor: selected ? "common.black" : "background.paper", color: selected ? "common.white" : "text.primary", borderColor: "#cfd8e3", "&:hover": { bgcolor: selected ? "#20252b" : "action.hover", borderColor: "#aebdcd" } }}
    >
      {label}
    </Button>
  );
}
