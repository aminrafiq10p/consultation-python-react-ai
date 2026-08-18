import { Alert, Box, Button, Card, CardContent, CircularProgress, Typography } from "@mui/material";
import { useCallback, useEffect, useRef, useState } from "react";

import { dashboardApi } from "./dashboardApi";
import type { DashboardMetrics } from "./dashboardTypes";

export interface DashboardMetricsService {
  getMetrics: () => Promise<DashboardMetrics>;
}

interface DashboardScreenProps {
  service?: DashboardMetricsService;
}

type DashboardState =
  | { status: "loading" }
  | { status: "success"; metrics: DashboardMetrics }
  | { status: "error" };

const metricCards = (metrics: DashboardMetrics) => [
  { label: "Total consultations", value: metrics.total_consultations.toString() },
  { label: "Booked appointments", value: metrics.booked_appointments.toString() },
  { label: "Conversion rate", value: `${metrics.conversion_rate.toFixed(2)}%` },
];

export function DashboardScreen({ service = dashboardApi }: DashboardScreenProps) {
  const [state, setState] = useState<DashboardState>({ status: "loading" });
  const requestId = useRef(0);

  const requestMetrics = useCallback(() => {
    const currentRequestId = ++requestId.current;

    service.getMetrics().then(
      (metrics) => {
        if (requestId.current === currentRequestId) {
          setState({ status: "success", metrics });
        }
      },
      () => {
        if (requestId.current === currentRequestId) {
          setState({ status: "error" });
        }
      },
    );
  }, [service]);

  const retry = () => {
    setState({ status: "loading" });
    requestMetrics();
  };

  useEffect(() => {
    requestMetrics();
    return () => {
      requestId.current += 1;
    };
  }, [requestMetrics]);

  return (
    <Box>
      <Typography component="h1" variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {state.status === "loading" && (
        <Box role="status" sx={{ display: "flex", gap: 2, alignItems: "center" }}>
          <CircularProgress size={24} />
          <span>Loading dashboard metrics…</span>
        </Box>
      )}

      {state.status === "error" && (
        <Alert
          severity="error"
          action={(
            <Button color="inherit" onClick={retry}>
              Retry
            </Button>
          )}
        >
          Dashboard metrics could not be loaded. Please try again.
        </Alert>
      )}

      {state.status === "success" && (
        <Box
          sx={{
            display: "grid",
            gap: 3,
            gridTemplateColumns: { xs: "1fr", sm: "repeat(3, 1fr)" },
          }}
        >
          {metricCards(state.metrics).map(({ label, value }) => (
            <Card key={label} variant="outlined">
              <CardContent>
                <Typography component="h2" variant="subtitle1" color="text.secondary">
                  {label}
                </Typography>
                <Typography variant="h4">{value}</Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );
}
