import { api, cleanParams, getData, getPage } from './client'
import type { Contact, ContactInput, ListParams } from './types'

export const contactsApi = {
  list: (params: ListParams) =>
    getPage<Contact>(api.get('/contacts/', { params: cleanParams(params) })),

  get: (id: number) => getData<Contact>(api.get(`/contacts/${id}/`)),

  create: (input: ContactInput) => getData<Contact>(api.post('/contacts/', input)),

  update: (id: number, input: Partial<ContactInput>) =>
    getData<Contact>(api.patch(`/contacts/${id}/`, input)),

  remove: (id: number) => api.delete(`/contacts/${id}/`),
}
