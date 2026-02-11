import { useEffect, useRef } from 'react'
import videojs from 'video.js'
import type Player from 'video.js/dist/types/player'
import 'video.js/dist/video-js.css'

interface VideoPlayerProps {
  videoId: string
  onTimeUpdate?: (currentTime: number) => void
  onReady?: () => void
  initialTime?: number
  seekTo?: number
}

export default function VideoPlayer({
  videoId,
  onTimeUpdate,
  onReady,
  initialTime,
  seekTo,
}: VideoPlayerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const playerRef = useRef<Player | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    // Only initialize if not already initialized (StrictMode safe)
    if (!playerRef.current) {
      const videoEl = document.createElement('video-js')
      videoEl.classList.add('vjs-big-play-centered')
      videoEl.setAttribute('data-testid', 'video-player')
      containerRef.current.appendChild(videoEl)

      const player = videojs(videoEl, {
        controls: true,
        responsive: true,
        fluid: true,
        sources: [
          {
            src: `/api/videos/${videoId}/stream`,
            type: 'video/mp4',
          },
        ],
      })

      player.ready(() => {
        if (initialTime != null) {
          player.currentTime(initialTime)
        }
        onReady?.()
      })

      player.on('timeupdate', () => {
        onTimeUpdate?.(player.currentTime() ?? 0)
      })

      playerRef.current = player
    }
    // Only initialize once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoId])

  useEffect(() => {
    return () => {
      const player = playerRef.current
      if (player && !player.isDisposed()) {
        player.dispose()
        playerRef.current = null
      }
    }
  }, [])

  useEffect(() => {
    if (seekTo != null && playerRef.current && !playerRef.current.isDisposed()) {
      playerRef.current.currentTime(seekTo)
    }
  }, [seekTo])

  return <div ref={containerRef} />
}
