import "./globals.css";
import { ThemeProvider } from "../components/theme-provider";  // <— relative path
// If you also use DesignModeProvider:
import { DesignModeProvider } from "../components/design-mode";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          {/* Remove this wrapper if you didn't add it */}
          <DesignModeProvider>{children}</DesignModeProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
