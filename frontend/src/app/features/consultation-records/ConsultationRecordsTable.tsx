import {
  Avatar,
  Button,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";

import type { ConsultationRecord } from "./consultationTypes";

interface ConsultationRecordsTableProps {
  records: ConsultationRecord[];
  onSelect: (consultationId: string) => void;
}

export function ConsultationRecordsTable({ records, onSelect }: ConsultationRecordsTableProps) {
  return (
    <TableContainer component={Paper} variant="outlined" sx={{ maxWidth: "100%", overflowX: "auto", boxShadow: "0 5px 18px rgba(26, 42, 65, 0.06)" }}>
      <Table aria-label="Consultation records" sx={{ minWidth: 680 }}>
        <TableHead>
          <TableRow sx={{ "& th": { bgcolor: "#fbfcfe", color: "text.secondary", fontSize: "0.72rem", fontWeight: 800, letterSpacing: "0.06em", textTransform: "uppercase", whiteSpace: "nowrap" } }}>
            <TableCell sx={{ width: "24%" }}>Patient name</TableCell>
            <TableCell sx={{ width: "27%" }}>Primary concern</TableCell>
            <TableCell sx={{ width: "31%" }}>Recommended procedure</TableCell>
            <TableCell>Status</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {records.map((record) => (
            <TableRow key={record.id} hover sx={{ "& td": { height: 76, borderColor: "divider" } }}>
              <TableCell>
                <Button
                  onClick={() => onSelect(record.id)}
                  color="inherit"
                  sx={{ justifyContent: "flex-start", gap: 1.25, px: 0.5, minWidth: 0, fontWeight: 700, textAlign: "left", whiteSpace: "nowrap" }}
                >
                  <Avatar aria-hidden sx={{ width: 34, height: 34, bgcolor: "primary.light", color: "primary.dark", fontSize: "0.75rem", fontWeight: 800 }}>{initials(record.patient_name)}</Avatar>
                  {record.patient_name}
                </Button>
              </TableCell>
              <TableCell sx={{ maxWidth: 260, overflowWrap: "anywhere" }}>{record.primary_concern}</TableCell>
              <TableCell sx={{ maxWidth: 300, overflowWrap: "anywhere" }}>{record.recommended_procedure}</TableCell>
              <TableCell><RecordStatusChip status={record.status} /></TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function initials(name: string) {
  return name.trim().split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("") || "?";
}

function RecordStatusChip({ status }: { status: ConsultationRecord["status"] }) {
  const styles = {
    PENDING: { bgcolor: "#fff4d6", color: "#805b00" },
    BOOKED: { bgcolor: "#e7efff", color: "#2453a6" },
    COMPLETED: { bgcolor: "#e8f5ed", color: "#24613c" },
  }[status];
  return <Chip label={status} size="small" sx={{ bgcolor: styles.bgcolor, color: styles.color, fontWeight: 800 }} />;
}
