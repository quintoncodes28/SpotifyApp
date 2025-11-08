"use client";
import * as React from "react";

type Mode = "current" | "legends";

const DesignModeCtx = React.createContext<{mode: Mode; setMode: (m: Mode)=>void}>({
  mode: "current",
  setMode: () => {},
});

export function DesignModeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setMode] = React.useState<Mode>("current");

  React.useEffect(() => {
    const el = document.documentElement;
    el.setAttribute("data-design", mode);
    return () => el.removeAttribute("data-design");
  }, [mode]);

  return (
    <DesignModeCtx.Provider value={{ mode, setMode }}>
      {children}
    </DesignModeCtx.Provider>
  );
}

export function useDesignMode() {
  return React.useContext(DesignModeCtx);
}
