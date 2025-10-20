import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      user: {
        id: 1,
        name: 'Usuário Demo',
        email: 'demo@transcricao.ai',
        initials: 'UD',
        avatar: null,
      },
      isAuthenticated: true,
      
      setUser: (user) => set({ user, isAuthenticated: true }),
      logout: () => set({ user: null, isAuthenticated: false }),
      updateProfile: (updates) => set((state) => ({
        user: { ...state.user, ...updates }
      })),
    }),
    {
      name: 'auth-storage',
    }
  )
)
