/**
 * TimestampLink component tests.
 *
 * P2-F01  test_timestamp_link_renders - displays formatted time
 * P2-F02  test_timestamp_click_seeks_video - click calls onClick
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import TimestampLink from '../../components/video/TimestampLink'

describe('P2-F01: TimestampLink renders', () => {
  it('displays "1:23" for seconds=83', () => {
    render(<TimestampLink seconds={83} onClick={() => {}} />)
    const link = screen.getByTestId('timestamp-link')
    expect(link).toHaveTextContent('1:23')
  })

  it('displays "0:00" for seconds=0', () => {
    render(<TimestampLink seconds={0} onClick={() => {}} />)
    const link = screen.getByTestId('timestamp-link')
    expect(link).toHaveTextContent('0:00')
  })
})

describe('P2-F02: TimestampLink click seeks video', () => {
  it('calls onClick callback when clicked', () => {
    const handleClick = vi.fn()
    render(<TimestampLink seconds={83} onClick={handleClick} />)

    fireEvent.click(screen.getByTestId('timestamp-link'))

    expect(handleClick).toHaveBeenCalledOnce()
  })
})
