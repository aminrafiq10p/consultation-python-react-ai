import { createTheme } from "@mui/material/styles";

export const appTheme = createTheme({
  palette: { mode: "light", primary: { main: "#1769d1", dark: "#0d4f9e", light: "#e7f0ff", contrastText: "#ffffff" }, background: { default: "#f5f7fb", paper: "#ffffff" }, text: { primary: "#1b2430", secondary: "#627080" }, divider: "#e2e7ee" },
  shape: { borderRadius: 12 },
  typography: { fontFamily: 'Inter, Roboto, "Helvetica Neue", Arial, sans-serif', h1: { fontSize: "clamp(1.75rem, 2.4vw, 2.25rem)", fontWeight: 750, letterSpacing: "-0.025em", lineHeight: 1.2 }, h2: { fontSize: "1.25rem", fontWeight: 700 }, h3: { fontSize: "1.05rem", fontWeight: 700 }, body1: { lineHeight: 1.55 }, body2: { lineHeight: 1.5 }, caption: { lineHeight: 1.4 } },
  components: {
    MuiCssBaseline: { styleOverrides: { "*, *::before, *::after": { boxSizing: "border-box" }, body: { margin: 0, backgroundColor: "#f5f7fb" }, "button:focus-visible, a:focus-visible, input:focus-visible, textarea:focus-visible, [role='button']:focus-visible": { outline: "3px solid rgba(23, 105, 209, 0.35)", outlineOffset: 2 } } },
    MuiCard: { styleOverrides: { root: { border: "1px solid #e2e7ee", borderRadius: 12, boxShadow: "0 5px 18px rgba(26, 42, 65, 0.06)" } } },
    MuiPaper: { styleOverrides: { root: { borderRadius: 12 }, outlined: { borderColor: "#e2e7ee" } } },
    MuiButton: { defaultProps: { disableElevation: true }, styleOverrides: { root: { minHeight: 42, borderRadius: 8, textTransform: "none", fontWeight: 700, paddingInline: 18, "&.Mui-disabled": { opacity: 0.58 } }, contained: { boxShadow: "0 5px 12px rgba(23, 105, 209, 0.2)" }, outlined: { borderColor: "#bdc9d7" } } },
    MuiTextField: { defaultProps: { size: "small", variant: "outlined" } },
    MuiOutlinedInput: { styleOverrides: { root: { borderRadius: 8, backgroundColor: "#ffffff", "& fieldset": { borderColor: "#cfd8e3" }, "&:hover fieldset": { borderColor: "#8da2ba" } } } },
    MuiChip: { styleOverrides: { root: { borderRadius: 999, fontWeight: 650 }, sizeSmall: { height: 26 } } },
    MuiCircularProgress: { defaultProps: { size: 24 } },
  },
});
