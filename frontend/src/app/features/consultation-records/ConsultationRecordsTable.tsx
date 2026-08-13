import {
  Button,
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
    <TableContainer component={Paper}>
      <Table aria-label="Consultation records">
        <TableHead>
          <TableRow>
            <TableCell>Patient name</TableCell>
            <TableCell>Primary concern</TableCell>
            <TableCell>Recommended procedure</TableCell>
            <TableCell>Status</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {records.map((record) => (
            <TableRow key={record.id} hover>
              <TableCell>
                <Button onClick={() => onSelect(record.id)}>{record.patient_name}</Button>
              </TableCell>
              <TableCell>{record.primary_concern}</TableCell>
              <TableCell>{record.recommended_procedure}</TableCell>
              <TableCell>{record.status}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
