import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { contactsApi } from '@/api/contacts.api'
import type { ContactInput, ListParams } from '@/api/types'

import { invalidateAfterWrite, queryKeys } from './queryKeys'

export function useContacts(params: ListParams) {
  return useQuery({
    queryKey: queryKeys.contacts(params),
    queryFn: () => contactsApi.list(params),
    placeholderData: keepPreviousData,
  })
}

function useInvalidateContacts() {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.contacts() })
    // Companies show contacts_count, so they are stale too.
    queryClient.invalidateQueries({ queryKey: queryKeys.companies() })
    queryClient.invalidateQueries({ queryKey: queryKeys.company() })
    invalidateAfterWrite(queryClient)
  }
}

export function useCreateContact() {
  const invalidate = useInvalidateContacts()
  return useMutation({
    mutationFn: (input: ContactInput) => contactsApi.create(input),
    onSuccess: invalidate,
  })
}

export function useUpdateContact() {
  const invalidate = useInvalidateContacts()
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: Partial<ContactInput> }) =>
      contactsApi.update(id, input),
    onSuccess: invalidate,
  })
}

export function useDeleteContact() {
  const invalidate = useInvalidateContacts()
  return useMutation({
    mutationFn: (id: number) => contactsApi.remove(id),
    onSuccess: invalidate,
  })
}
