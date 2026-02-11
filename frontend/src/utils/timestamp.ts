/**
 * Convert seconds to MM:SS format.
 * Examples: 125 → "2:05", 0 → "0:00", 65 → "1:05", 3661 → "61:01"
 */
export function formatTimestamp(seconds: number): string {
  const totalSeconds = Math.floor(seconds)
  const minutes = Math.floor(totalSeconds / 60)
  const secs = totalSeconds % 60
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

/**
 * Convert MM:SS format back to seconds.
 * Examples: "2:05" → 125, "0:00" → 0, "1:05" → 65
 */
export function parseTimestamp(formatted: string): number {
  const [minutes, seconds] = formatted.split(':').map(Number)
  return minutes * 60 + seconds
}
