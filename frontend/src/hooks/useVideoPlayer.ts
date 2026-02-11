import { useCallback, useRef, useState } from 'react'

export interface UseVideoPlayerReturn {
  currentTime: number
  isPlaying: boolean
  seek: (time: number) => void
  videoRef: React.RefObject<HTMLVideoElement | null>
  onTimeUpdate: () => void
}

export function useVideoPlayer(): UseVideoPlayerReturn {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)

  const seek = useCallback((time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time
      setCurrentTime(time)
    }
  }, [])

  const onTimeUpdate = useCallback(() => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime)
      setIsPlaying(!videoRef.current.paused)
    }
  }, [])

  return { currentTime, isPlaying, seek, videoRef, onTimeUpdate }
}
