import { useEffect, useRef } from 'react'
import videojs from 'video.js'
import type Player from 'video.js/dist/types/player'
import 'video.js/dist/video-js.css'

interface VideoPlayerProps {
  videoId: string
  onTimeUpdate?: (currentTime: number) => void
  onReady?: () => void
  initialTime?: number
}

export default function VideoPlayer({
  videoId,
  onTimeUpdate,
  onReady,
  initialTime,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const playerRef = useRef<Player | null>(null)

  useEffect(() => {
    if (!videoRef.current) return

    const player = videojs(videoRef.current, {
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

    return () => {
      if (playerRef.current) {
        playerRef.current.dispose()
        playerRef.current = null
      }
    }
    // Only initialize once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoId])

  return (
    <div data-vjs-player>
      <video
        ref={videoRef}
        data-testid="video-player"
        className="video-js vjs-big-play-centered"
      />
    </div>
  )
}
