import api from './api'

export const authService = {
  async getConfig() {
    const { data } = await api.get('/auth/config')
    return data
  },

  async login(username, password) {
    const { data } = await api.post('/auth/login', { username, password })
    return data
  },

  async me() {
    const { data } = await api.get('/auth/me')
    return data
  },
}
