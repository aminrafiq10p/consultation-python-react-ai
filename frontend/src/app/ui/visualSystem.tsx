import { Box, Chip, Paper, Typography } from "@mui/material";
import type { ReactNode } from "react";

export function Surface({ children, ...props }: { children: ReactNode } & React.ComponentProps<typeof Paper>) {
  return <Paper variant="outlined" {...props}>{children}</Paper>;
}

export function PageHeader({ title, subtitle, children }: { title: string; subtitle?: string; children?: ReactNode }) {
  return (
    <Box sx={{ display: "flex", flexDirection: { xs: "column", sm: "row" }, justifyContent: "space-between", alignItems: { xs: "stretch", sm: "flex-start" }, gap: 2, mb: 3 }}>
      <div>
        <Typography component="h1" variant="h1">{title}</Typography>
        {subtitle && <Typography color="text.secondary" sx={{ mt: 0.75 }}>{subtitle}</Typography>}
      </div>
      {children}
    </Box>
  );
}

export function StatusChip({ label }: { label: string }) {
  return <Chip label={label} size="small" sx={{ bgcolor: "#edf1f5", color: "text.primary" }} />;
}
