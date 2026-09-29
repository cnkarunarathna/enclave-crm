import { zodResolver } from '@hookform/resolvers/zod'
import { AlertCircle } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { ApiError } from '@/api/errors'
import { FormField } from '@/components/common/FormField'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Spinner } from '@/components/ui/spinner'
import { useAuth } from '@/hooks/useAuth'

const loginSchema = z.object({
  email: z.email('Enter a valid email address.'),
  password: z.string().min(1, 'Enter your password.'),
})
type LoginValues = z.infer<typeof loginSchema>

// Shown in development only, so reviewers can try every role quickly.
const DEMO_ACCOUNTS = [
  'admin@acme.test',
  'manager@acme.test',
  'staff@acme.test',
  'admin@bluesky.test',
]
const DEMO_PASSWORD = 'Passw0rd!123'

export function LoginPage() {
  const { login } = useAuth()
  const [serverError, setServerError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) })

  const onSubmit = async ({ email, password }: LoginValues) => {
    setServerError(null)
    try {
      await login(email, password)
      // PublicOnlyRoute redirects once the status becomes "authenticated".
    } catch (error) {
      setServerError(error instanceof ApiError ? error.message : 'Sign in failed.')
    }
  }

  const fillDemo = (email: string) => {
    setValue('email', email, { shouldValidate: true })
    setValue('password', DEMO_PASSWORD, { shouldValidate: true })
  }

  return (
    <div className="bg-muted/40 flex min-h-svh items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex items-center justify-center gap-2">
          <div className="bg-primary text-primary-foreground flex size-9 items-center justify-center rounded-md font-bold">
            E
          </div>
          <span className="text-lg font-semibold">Enclave CRM</span>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Sign in</CardTitle>
            <CardDescription>Use your work email and password.</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <CardContent className="flex flex-col gap-4">
              {serverError && (
                <Alert variant="destructive">
                  <AlertCircle />
                  <AlertDescription>{serverError}</AlertDescription>
                </Alert>
              )}
              <FormField label="Email" htmlFor="email" error={errors.email?.message}>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  autoFocus
                  aria-invalid={!!errors.email}
                  {...register('email')}
                />
              </FormField>
              <FormField label="Password" htmlFor="password" error={errors.password?.message}>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  aria-invalid={!!errors.password}
                  {...register('password')}
                />
              </FormField>
            </CardContent>
            <CardFooter className="mt-6">
              <Button type="submit" className="w-full" size="lg" disabled={isSubmitting}>
                {isSubmitting && <Spinner />}
                {isSubmitting ? 'Signing in…' : 'Sign in'}
              </Button>
            </CardFooter>
          </form>
        </Card>

        {import.meta.env.DEV && (
          <div className="text-muted-foreground mt-6 rounded-lg border border-dashed p-4 text-sm">
            <p className="text-foreground mb-2 font-medium">Demo accounts (dev only)</p>
            <p className="mb-3">
              Password: <code className="text-foreground">{DEMO_PASSWORD}</code>. Run{' '}
              <code className="text-foreground">make seed</code> first.
            </p>
            <div className="flex flex-wrap gap-2">
              {DEMO_ACCOUNTS.map((email) => (
                <Button key={email} variant="outline" size="xs" onClick={() => fillDemo(email)}>
                  {email}
                </Button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
