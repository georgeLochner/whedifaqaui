/**
 * Timestamp formatting and parsing utility tests.
 *
 * P2-U01  test_timestamp_formatting - seconds → MM:SS
 * P2-U02  test_timestamp_parsing - MM:SS → seconds
 */

import { describe, it, expect } from 'vitest'
import { formatTimestamp, parseTimestamp } from '../../utils/timestamp'

describe('formatTimestamp', () => {
  it('P2-U01: converts seconds to MM:SS format', () => {
    expect(formatTimestamp(125)).toBe('2:05')
    expect(formatTimestamp(0)).toBe('0:00')
    expect(formatTimestamp(65)).toBe('1:05')
    expect(formatTimestamp(3661)).toBe('61:01')
  })

  it('handles fractional seconds by flooring', () => {
    expect(formatTimestamp(125.7)).toBe('2:05')
    expect(formatTimestamp(59.9)).toBe('0:59')
  })

  it('pads single-digit seconds with leading zero', () => {
    expect(formatTimestamp(61)).toBe('1:01')
    expect(formatTimestamp(3)).toBe('0:03')
  })
})

describe('parseTimestamp', () => {
  it('P2-U02: converts MM:SS format to seconds', () => {
    expect(parseTimestamp('2:05')).toBe(125)
    expect(parseTimestamp('0:00')).toBe(0)
    expect(parseTimestamp('1:05')).toBe(65)
  })

  it('handles large minute values', () => {
    expect(parseTimestamp('61:01')).toBe(3661)
  })
})
