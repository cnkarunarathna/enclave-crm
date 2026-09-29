import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { companiesApi } from '@/api/companies.api'
import type { CompanyInput, ListParams } from '@/api/types'

import { invalidateAfterWrite, queryKeys } from './queryKeys'

export function useCompanies(params: ListParams) {
  return useQuery({
    queryKey: queryKeys.companies(params),
    queryFn: () => companiesApi.list(params),
    placeholderData: keepPreviousData, // keep the old page visible while the next loads
  })
}

export function useCompanyFacets() {
  return useQuery({ queryKey: queryKeys.companyFacets(), queryFn: companiesApi.facets })
}

export function useCompany(id: number) {
  return useQuery({
    queryKey: queryKeys.company(id),
    queryFn: () => companiesApi.get(id),
    enabled: Number.isFinite(id),
  })
}

function useInvalidateCompanies() {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.companies() }) // lists + facets
    queryClient.invalidateQueries({ queryKey: queryKeys.company() })
    invalidateAfterWrite(queryClient)
  }
}

export function useCreateCompany() {
  const invalidate = useInvalidateCompanies()
  return useMutation({
    mutationFn: (input: CompanyInput) => companiesApi.create(input),
    onSuccess: invalidate,
  })
}

export function useUpdateCompany() {
  const invalidate = useInvalidateCompanies()
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: Partial<CompanyInput> }) =>
      companiesApi.update(id, input),
    onSuccess: invalidate,
  })
}

export function useDeleteCompany() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => companiesApi.remove(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.companies() })
      // Mark the deleted company stale without refetching it: the detail page is about
      // to navigate away, and a refetch would briefly flash "Company not found".
      queryClient.invalidateQueries({ queryKey: queryKeys.company(id), refetchType: 'none' })
      // Deleting a company also soft-deletes its contacts on the server.
      queryClient.invalidateQueries({ queryKey: queryKeys.contacts() })
      invalidateAfterWrite(queryClient)
    },
  })
}
