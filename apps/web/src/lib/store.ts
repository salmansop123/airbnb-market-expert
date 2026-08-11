import { create } from "zustand";
import { persist } from "zustand/middleware";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: { id: string; email: string; full_name?: string; plan: string; is_verified: boolean } | null;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: AuthState["user"]) => void;
  logout: () => void;
};

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
      setUser: (user) => set({ user }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: "stayprice-auth" }
  )
);

type UiState = {
  sidebarOpen: boolean;
  wizardStep: number;
  setSidebarOpen: (v: boolean) => void;
  setWizardStep: (n: number) => void;
};

export const useUi = create<UiState>((set) => ({
  sidebarOpen: true,
  wizardStep: 1,
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  setWizardStep: (wizardStep) => set({ wizardStep }),
}));
