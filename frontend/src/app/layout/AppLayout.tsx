import {
  AppBar, Box, Button, Divider, Drawer, IconButton, List, ListItemButton,
  ListItemIcon, ListItemText, SvgIcon, Toolbar, Typography, useMediaQuery, useTheme,
} from "@mui/material";
import { useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";

const drawerWidth = 264;
const navigationItems = [
  { label: "Dashboard", destination: "/dashboard", section: "dashboard" },
  { label: "Consultations", destination: "/consultations", section: "consultations" },
] as const;

function DashboardIcon() {
  return <SvgIcon fontSize="small"><path d="M4 4h6v6H4V4Zm10 0h6v6h-6V4ZM4 14h6v6H4v-6Zm10 0h6v6h-6v-6Z" /></SvgIcon>;
}

function ConsultationsIcon() {
  return <SvgIcon fontSize="small"><path d="M9 3h6l1 2h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h3l1-2Zm1.2 2-.5 1h4.6l-.5-1h-3.6ZM11 9v3H8v2h3v3h2v-3h3v-2h-3V9h-2Z" /></SvgIcon>;
}

function MenuIcon() {
  return <SvgIcon><path d="M3 6h18v2H3V6Zm0 5h18v2H3v-2Zm0 5h18v2H3v-2Z" /></SvgIcon>;
}

function SidebarContent({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  const isActive = (section: (typeof navigationItems)[number]["section"]) =>
    section === "dashboard"
      ? pathname === "/dashboard"
      : pathname === "/consultations" || pathname.startsWith("/consultations/");

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Box sx={{ px: 3, pt: 3.5, pb: 2.5 }}>
        <Typography variant="h6" sx={{ color: "primary.dark", fontWeight: 800, lineHeight: 1.1 }}>
          Auvia Admin
        </Typography>
        <Typography variant="caption" color="text.secondary">AI Consultation Platform</Typography>
      </Box>
      <Box sx={{ px: 2, pb: 3 }}>
        <Button
          fullWidth
          variant="contained"
          color="inherit"
          disabled
          sx={{
            bgcolor: "common.black", color: "common.white", py: 1.25, fontWeight: 700,
            "&.Mui-disabled": { bgcolor: "common.black", color: "common.white", opacity: 1 },
          }}
        >
          + New Consult
        </Button>
      </Box>
      <Box component="nav" aria-label="Primary navigation" sx={{ px: 2 }}>
        <List disablePadding>
          {navigationItems.map(({ label, destination, section }) => {
            const active = isActive(section);
            return (
              <ListItemButton
                key={destination}
                component={Link}
                to={destination}
                selected={active}
                aria-current={active ? "page" : undefined}
                onClick={onNavigate}
                sx={{
                  borderRadius: 2, mb: 1, minHeight: 48,
                  color: active ? "primary.contrastText" : "text.primary",
                  "&.Mui-selected": { bgcolor: "primary.main", boxShadow: "0 6px 16px rgba(25, 118, 210, 0.22)" },
                  "&.Mui-selected:hover": { bgcolor: "primary.dark" },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40, color: "inherit" }}>
                  {section === "dashboard" ? <DashboardIcon /> : <ConsultationsIcon />}
                </ListItemIcon>
                <ListItemText primary={label} slotProps={{ primary: { sx: { fontWeight: active ? 700 : 500 } } }} />
              </ListItemButton>
            );
          })}
        </List>
      </Box>
      <Box sx={{ mt: "auto", px: 2, pb: 3 }}>
        <Divider sx={{ mb: 2 }} />
        <Typography variant="caption" color="text.secondary">Clinical Intelligence</Typography>
      </Box>
    </Box>
  );
}

export function AppLayout() {
  const theme = useTheme();
  const desktop = useMediaQuery(theme.breakpoints.up("md"));
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#f5f7fb" }}>
      {!desktop && (
        <AppBar position="sticky" elevation={0} sx={{ bgcolor: "background.paper", color: "text.primary", borderBottom: 1, borderColor: "divider" }}>
          <Toolbar>
            <IconButton edge="start" aria-label="Open navigation" onClick={() => setMobileOpen(true)} sx={{ mr: 2 }}>
              <MenuIcon />
            </IconButton>
            <Box>
              <Typography variant="h6" sx={{ color: "primary.dark", fontWeight: 800, lineHeight: 1.1 }}>Auvia Admin</Typography>
              <Typography variant="caption" color="text.secondary">AI Consultation Platform</Typography>
            </Box>
          </Toolbar>
        </AppBar>
      )}

      {desktop ? (
        <Drawer
          variant="permanent"
          slotProps={{ paper: { component: "aside", "aria-label": "Application sidebar" } }}
          sx={{
            width: drawerWidth, flexShrink: 0,
            "& .MuiDrawer-paper": { width: drawerWidth, boxSizing: "border-box", borderRightColor: "divider", bgcolor: "#fbfcfe" },
          }}
        >
          <SidebarContent pathname={location.pathname} />
        </Drawer>
      ) : (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          slotProps={{ paper: { component: "aside", "aria-label": "Application sidebar" } }}
          sx={{ "& .MuiDrawer-paper": { width: drawerWidth } }}
        >
          <SidebarContent pathname={location.pathname} onNavigate={() => setMobileOpen(false)} />
        </Drawer>
      )}

      <Box
        component="main"
        sx={{
          ml: desktop ? `${drawerWidth}px` : 0,
          minHeight: desktop ? "100vh" : "calc(100vh - 64px)",
          px: { xs: 2, sm: 3, md: 5 }, py: { xs: 3, md: 4 },
        }}
      >
        <Box sx={{ width: "100%", maxWidth: 1280, mx: "auto" }}><Outlet /></Box>
      </Box>
    </Box>
  );
}
