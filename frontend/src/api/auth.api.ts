import { api, getData } from './client'
import type { LoginResponse, User } from './types'

export const authApi = {
  login: (email: string, password: string) =>
    getData<LoginResponse>(api.post('/auth/login/', { email, password })),

  logout: (refresh: string) => api.post('/auth/logout/', { refresh }),

  me: () => getData<User>(api.get('/auth/me/')),
}
