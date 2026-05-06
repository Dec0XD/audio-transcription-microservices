import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      token: null,
      authMode: 'permissive',
      isAuthenticated: false,
      
      setAuthMode: (authMode) => set({ authMode }),
      setUser: (user) => set({ user, isAuthenticated: true }),
      setSession: (user, token) => {
        localStorage.setItem('token', token)
        set({
          token,
          user: {
            id: 1,
            name: user?.username || 'Usuário',
            email: `${user?.username || 'user'}@transcricao.ai`,
            initials: (user?.username || 'U').slice(0, 2).toUpperCase(),
            avatar: null,
            roles: user?.roles || [],
            scopes: user?.scopes || [],
          },
          isAuthenticated: true,
        })
      },
      enableDemoSession: () => set({
        user: {
          id: 1,
          name: 'Usuário Demo',
          email: 'demo@transcricao.ai',
          initials: 'UD',
          avatar: null,
          roles: ['user'],
          scopes: ['transcribe', 'meeting_minutes', 'read_transcriptions'],
        },
        isAuthenticated: true,
      }),
      logout: () => {
        localStorage.removeItem('token')
        set({ user: null, token: null, isAuthenticated: false })
      },
      updateProfile: (updates) => set((state) => ({
        user: { ...state.user, ...updates }
      })),
    }),
    {
      name: 'auth-storage',
    }
  )
)
