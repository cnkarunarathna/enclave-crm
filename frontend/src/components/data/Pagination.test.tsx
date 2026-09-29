import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Pagination } from './Pagination'

describe('Pagination', () => {
  it('shows the visible range and moves between pages', async () => {
    const onPageChange = vi.fn()
    render(
      <Pagination
        meta={{ count: 23, page: 2, page_size: 10, total_pages: 3 }}
        onPageChange={onPageChange}
      />,
    )

    expect(screen.getByRole('navigation')).toHaveTextContent('Showing 11–20 of 23')
    await userEvent.click(screen.getByRole('button', { name: /next/i }))
    await userEvent.click(screen.getByRole('button', { name: /previous/i }))
    expect(onPageChange.mock.calls).toEqual([[3], [1]])
  })

  it('disables Next on the last page', () => {
    render(
      <Pagination
        meta={{ count: 23, page: 3, page_size: 10, total_pages: 3 }}
        onPageChange={() => {}}
      />,
    )

    expect(screen.getByRole('navigation')).toHaveTextContent('Showing 21–23 of 23')
    expect(screen.getByRole('button', { name: /next/i })).toBeDisabled()
  })

  it('renders nothing when everything fits on one page', () => {
    const { container } = render(
      <Pagination
        meta={{ count: 4, page: 1, page_size: 10, total_pages: 1 }}
        onPageChange={() => {}}
      />,
    )
    expect(container).toBeEmptyDOMElement()
  })
})
