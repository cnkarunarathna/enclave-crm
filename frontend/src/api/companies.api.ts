import { api, cleanParams, getData, getPage } from './client'
import type { Company, CompanyFacets, CompanyInput, ListParams } from './types'

/** Send multipart only when a file is involved; JSON otherwise. */
function toPayload(input: Partial<CompanyInput>) {
  if (!(input.logo instanceof File)) {
    // A file can't travel as JSON. No new file = keep the current logo (unless remove_logo).
    const json = { ...input }
    delete json.logo
    return json
  }
  const form = new FormData()
  Object.entries(input).forEach(([key, value]) => {
    if (value === undefined || value === null) return
    form.append(key, value instanceof File ? value : String(value))
  })
  return form
}

export const companiesApi = {
  list: (params: ListParams) =>
    getPage<Company>(api.get('/companies/', { params: cleanParams(params) })),

  /** Distinct industries/countries in use, for the filter dropdowns. */
  facets: () => getData<CompanyFacets>(api.get('/companies/facets/')),

  get: (id: number) => getData<Company>(api.get(`/companies/${id}/`)),

  create: (input: CompanyInput) => getData<Company>(api.post('/companies/', toPayload(input))),

  update: (id: number, input: Partial<CompanyInput>) =>
    getData<Company>(api.patch(`/companies/${id}/`, toPayload(input))),

  remove: (id: number) => api.delete(`/companies/${id}/`),
}
