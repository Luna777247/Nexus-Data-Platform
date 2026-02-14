
import { create } from 'zustand';
import { User, UserRole } from './types';

interface AppState {
  user: User | null;
  isAuthenticated: boolean;
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  setAuthenticated: (user: User | null) => void;
  toggleTheme: () => void;
  toggleSidebar: () => void;
  logout: () => void;
}

export const useStore = create<AppState>((set) => ({
  user: null,
  isAuthenticated: false,
  theme: 'light',
  sidebarOpen: true,
  setAuthenticated: (user) => set({ user, isAuthenticated: !!user }),
  toggleTheme: () => set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  logout: () => set({ user: null, isAuthenticated: false }),
}));
