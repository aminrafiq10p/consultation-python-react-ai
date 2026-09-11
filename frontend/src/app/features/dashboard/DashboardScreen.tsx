import {
  Alert, Box, Button, Card, CardContent, CircularProgress, Divider,
  Link as MuiLink, Stack, SvgIcon, Typography,
} from "@mui/material";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { dashboardApi } from "./dashboardApi";
import type { DashboardActivity, DashboardResponse, DashboardTrend } from "./dashboardTypes";
import { PageHeader, Surface, StatusChip } from "../../ui/visualSystem";

export interface DashboardMetricsService { getMetrics: () => Promise<DashboardResponse>; }
interface DashboardScreenProps { service?: DashboardMetricsService; }
type DashboardState = { status: "loading" } | { status: "success"; metrics: DashboardResponse } | { status: "error" };

const metricCards = (metrics: DashboardResponse) => [
  { label: "Total Consultations", value: metrics.total_consultations.toString(), detail: "All recorded consultations" },
  { label: "Booked Appointments", value: metrics.booked_appointments.toString(), detail: "Appointments created" },
  { label: "Conversion Rate", value: `${metrics.conversion_rate.toFixed(2)}%`, detail: "Booked appointments / consultations" },
];

function EmptyState({ message }: { message: string }) { return <Typography color="text.secondary" sx={{ py: 5, textAlign: "center" }}>{message}</Typography>; }
function formatDay(day: string) { return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(new Date(`${day}T00:00:00Z`)); }
function formatTimestamp(timestamp: string) { return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(timestamp)); }
function initials(name: string) { return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase(); }

function TrendChart({ trends }: { trends: DashboardTrend[] }) {
  if (trends.length === 0) return <EmptyState message="No trend data yet." />;
  const maximum = Math.max(...trends.map((trend) => trend.consultation_count), 1);
  const accessibleValues = trends.map((trend) => `${formatDay(trend.day)}: ${trend.consultation_count}`).join("; ");
  return <Box role="img" aria-label={`Consultation trends for the last 30 days. ${trends.length} populated days. ${accessibleValues}.`} sx={{ minWidth: 0 }}><Box sx={{ display: "flex", alignItems: "end", gap: { xs: 1, sm: 1.75 }, height: 220, px: 1, borderBottom: 1, borderColor: "divider" }}>{trends.map((trend, index) => { const height = Math.max((trend.consultation_count / maximum) * 100, 8); return <Box key={trend.day} sx={{ flex: "1 1 0", minWidth: 0, height: "100%", display: "flex", flexDirection: "column", justifyContent: "end", alignItems: "center", gap: 0.75 }}><Typography variant="caption" sx={{ fontWeight: 700, color: index === trends.length - 1 ? "primary.dark" : "text.secondary" }}>{trend.consultation_count}</Typography><Box aria-hidden sx={{ width: "min(38px, 72%)", height: `${height}%`, minHeight: 18, bgcolor: index === trends.length - 1 ? "primary.main" : "primary.light", borderRadius: "6px 6px 0 0" }} /><Typography variant="caption" color="text.secondary" sx={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "100%" }}>{formatDay(trend.day)}</Typography></Box>; })}</Box><Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>Showing populated days in the rolling 30-day range</Typography></Box>;
}

function formatActivity(activity: DashboardActivity) { return { conversation_started: "Consultation conversation started", consultation_completed: "Consultation completed", appointment_booked: "Appointment booked" }[activity.activity_type]; }
function ActivityIcon({ type }: { type: DashboardActivity["activity_type"] }) { const path = type === "appointment_booked" ? "M7 2h2v2h6V2h2v2h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2V2Zm-2 8v10h14V10H5Z" : type === "consultation_completed" ? "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm-1 5h2v6h-2V7Zm0 8h2v2h-2v-2Z" : "M4 4h16v12H7l-3 3V4Zm3 4v2h10V8H7Z"; return <SvgIcon fontSize="small" aria-hidden><path d={path} /></SvgIcon>; }

function DashboardContent({ metrics }: { metrics: DashboardResponse }) {
  return <><Box sx={{ display: "grid", gap: 2.5, gridTemplateColumns: { xs: "1fr", sm: "repeat(3, minmax(0, 1fr))" }, mb: 3.5 }}>{metricCards(metrics).map(({ label, value, detail }) => <Card key={label}><CardContent sx={{ p: { xs: 2.25, sm: 2.75 }, "&:last-child": { pb: { xs: 2.25, sm: 2.75 } } }}><Typography component="h2" variant="overline" color="text.secondary" sx={{ fontWeight: 800, letterSpacing: "0.08em" }}>{label}</Typography><Typography sx={{ mt: 1, fontSize: { xs: "2rem", sm: "2.25rem" }, fontWeight: 800, letterSpacing: "-0.04em" }}>{value}</Typography><Typography variant="caption" color="text.secondary">{detail}</Typography></CardContent></Card>)}</Box>
    <Box sx={{ display: "grid", gap: 2.5, gridTemplateColumns: { xs: "1fr", lg: "minmax(0, 1.75fr) minmax(300px, 0.9fr)" }, alignItems: "start" }}><Stack spacing={2.5}><Surface sx={{ p: { xs: 2, sm: 2.75 } }}><Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 2, mb: 2.5 }}><Box><Typography component="h2" variant="h2">Consultation Trends</Typography><Typography variant="body2" color="text.secondary">Last 30 days</Typography></Box><StatusChip label="Rolling range" /></Box><TrendChart trends={metrics.consultation_trends} /></Surface>
      <Surface sx={{ p: { xs: 2, sm: 2.75 }, borderLeft: { md: "3px solid" }, borderLeftColor: { md: "primary.main" } }}><Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 2, mb: 2 }}><Typography component="h2" variant="h2">Pending Clinical Reviews</Typography>{metrics.pending_clinical_reviews.length > 0 && <StatusChip label={`${metrics.pending_clinical_reviews.length} pending`} />}</Box>{metrics.pending_clinical_reviews.length === 0 ? <EmptyState message="No pending clinical reviews." /> : <Stack divider={<Divider flexItem />} spacing={0}>{metrics.pending_clinical_reviews.map((review) => <MuiLink key={review.consultation_id} component={Link} to={`/consultations/${review.consultation_id}`} underline="none" color="inherit" sx={{ display: "block", py: 1.5, px: 1, borderRadius: 1, "&:hover": { bgcolor: "action.hover" } }}><Box sx={{ display: "flex", gap: 1.5, alignItems: "center" }}><Box aria-hidden sx={{ width: 38, height: 38, borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: "primary.light", color: "primary.dark", fontWeight: 800, flexShrink: 0 }}>{initials(review.patient_name)}</Box><Box sx={{ minWidth: 0, flex: 1 }}><Typography noWrap sx={{ fontWeight: 700 }}>{review.patient_name}</Typography><Typography variant="body2" color="text.secondary" noWrap>{review.primary_concern}{review.recommended_procedure ? ` · ${review.recommended_procedure}` : ""}</Typography></Box><Typography aria-hidden color="primary.main" sx={{ fontSize: "1.5rem" }}>→</Typography></Box></MuiLink>)}</Stack>}</Surface></Stack>
      <Surface sx={{ p: { xs: 2, sm: 2.75 } }}><Typography component="h2" variant="h2" sx={{ mb: 2 }}>Recent Activity</Typography>{metrics.recent_activity.length === 0 ? <EmptyState message="No recent activity yet." /> : <Stack spacing={0}>{metrics.recent_activity.map((activity, index) => <Box key={`${activity.timestamp}-${activity.consultation_id}-${activity.activity_type}`} sx={{ display: "flex", gap: 1.5, minWidth: 0 }}><Box sx={{ display: "flex", flexDirection: "column", alignItems: "center" }}><Box sx={{ width: 34, height: 34, borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: "primary.light", color: "primary.dark" }}><ActivityIcon type={activity.activity_type} /></Box>{index < metrics.recent_activity.length - 1 && <Box sx={{ width: 1, flex: 1, bgcolor: "divider", minHeight: 28 }} />}</Box><MuiLink component={Link} to={`/consultations/${activity.consultation_id}`} underline="none" color="inherit" sx={{ py: 0.25, pb: 2.25, minWidth: 0, "&:hover": { color: "primary.main" } }}><Typography variant="body2" sx={{ fontWeight: 700 }}>{formatActivity(activity)}</Typography><Typography variant="caption" color="text.secondary">{formatTimestamp(activity.timestamp)}</Typography></MuiLink></Box>)}</Stack>}</Surface></Box></>;
}

export function DashboardScreen({ service = dashboardApi }: DashboardScreenProps) {
  const [state, setState] = useState<DashboardState>({ status: "loading" }); const requestId = useRef(0);
  const requestMetrics = useCallback(() => { const currentRequestId = ++requestId.current; service.getMetrics().then((metrics) => { if (requestId.current === currentRequestId) setState({ status: "success", metrics }); }, () => { if (requestId.current === currentRequestId) setState({ status: "error" }); }); }, [service]);
  useEffect(() => { requestMetrics(); return () => { requestId.current += 1; }; }, [requestMetrics]);
  return <Box><PageHeader title="Dashboard" subtitle="A clear view of your consultation practice." />{state.status === "loading" && <Box role="status" sx={{ display: "flex", gap: 2, alignItems: "center", py: 4 }}><CircularProgress size={24} /><span>Loading dashboard…</span></Box>}{state.status === "error" && <Alert severity="error" action={<Button color="inherit" onClick={() => { setState({ status: "loading" }); requestMetrics(); }}>Retry</Button>}>Dashboard data could not be loaded. Please try again.</Alert>}{state.status === "success" && <DashboardContent metrics={state.metrics} />}</Box>;
}
