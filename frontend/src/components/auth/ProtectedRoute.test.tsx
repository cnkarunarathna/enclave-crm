import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { AuthContext, type AuthContextValue, type AuthStatus } from '@/context/auth-context'

import { ProtectedRoute } from './ProtectedRoute'
import { RoleGate } from './RoleGate'

function renderWithAuth(status: AuthStatus, path = '/private', canRead = true) {
  const auth: AuthContextValue = {
    status,
    user: null,
    login: async () => {},
    logout: async () => {},
    can: () => canRead,
  }
  return render(
    <AuthContext.Provider value={auth}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/login" element={<p>Login page</p>} />
          <Route
            path="/private"
            element={
              <ProtectedRoute>
                <RoleGate resource="activity_log" verb="read" fallback={<p>Forbidden</p>}>
                  <p>Secret content</p>
                </RoleGate>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

describe('ProtectedRoute', () => {
  it('redirects anonymous users to /login', () => {
    renderWithAuth('anonymous')
    expect(screen.getByText('Login page')).toBeInTheDocument()
    expect(screen.queryByText('Secret content')).not.toBeInTheDocument()
  })

  it('shows a spinner while the session is being restored', () => {
    renderWithAuth('loading')
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.queryByText('Login page')).not.toBeInTheDocument()
  })

  it('renders the page for signed-in users', () => {
    renderWithAuth('authenticated')
    expect(screen.getByText('Secret content')).toBeInTheDocument()
  })

  it('RoleGate shows the fallback when the role lacks the capability', () => {
    renderWithAuth('authenticated', '/private', false)
    expect(screen.getByText('Forbidden')).toBeInTheDocument()
    expect(screen.queryByText('Secret content')).not.toBeInTheDocument()
  })
})
