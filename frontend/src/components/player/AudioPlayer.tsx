import { useEffect, useRef, useState } from "react";
import { useAudioStore } from "@/store/useAudioStore";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  Maximize2,
  Minimize2,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

export function AudioPlayer() {
  const {
    currentChapter,
    isPlaying,
    volume,
    playbackRate,
    currentTime,
    isExpanded,
    togglePlay,
    setIsPlaying,
    nextChapter,
    prevChapter,
    setCurrentTime,
    setDuration,
    duration,
    toggleExpanded,
    bookIsbn,
  } = useAudioStore();

  const audioRef = useRef<HTMLAudioElement>(null);
  const [localTime, setLocalTime] = useState(currentTime);
  const [isDragging, setIsDragging] = useState(false);

  // Sync audio element with store state
  useEffect(() => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.play().catch(() => setIsPlaying(false));
      } else {
        audioRef.current.pause();
      }
    }
  }, [isPlaying, setIsPlaying]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
  }, [volume]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate]);

  // Media Session API
  useEffect(() => {
    if ("mediaSession" in navigator && currentChapter) {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: currentChapter.title,
        artist: `Chapter ${currentChapter.chapter_number}`,
        album: "BookBytes Audio",
        artwork: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
        ],
      });

      navigator.mediaSession.setActionHandler("play", () => {
        setIsPlaying(true);
      });
      navigator.mediaSession.setActionHandler("pause", () => {
        setIsPlaying(false);
      });
      navigator.mediaSession.setActionHandler("previoustrack", () => {
        prevChapter();
      });
      navigator.mediaSession.setActionHandler("nexttrack", () => {
        nextChapter();
      });
      navigator.mediaSession.setActionHandler("seekto", (details) => {
        if (details.seekTime && audioRef.current) {
          audioRef.current.currentTime = details.seekTime;
          setCurrentTime(details.seekTime);
        }
      });
    }
  }, [currentChapter, setIsPlaying, prevChapter, nextChapter, setCurrentTime]);

  // Handle source change
  useEffect(() => {
    if (currentChapter && audioRef.current) {
      // Construct the audio URL.
      // Assuming the backend serves it at /api/audio/<isbn>/<chapter_number>
      const audioUrl = `/api/audio/${bookIsbn}/${currentChapter.chapter_number}`;

      if (audioRef.current.src !== window.location.origin + audioUrl) {
        audioRef.current.src = audioUrl;
        if (isPlaying) {
          audioRef.current.play().catch(console.error);
        }
      }
    }
  }, [currentChapter, bookIsbn, isPlaying]);

  // Handle seeking from other components (like prevChapter restart)
  useEffect(() => {
    if (
      audioRef.current &&
      Math.abs(audioRef.current.currentTime - currentTime) > 1 &&
      !isDragging
    ) {
      audioRef.current.currentTime = currentTime;
    }
  }, [currentTime, isDragging]);

  const handleTimeUpdate = () => {
    if (audioRef.current && !isDragging) {
      const time = audioRef.current.currentTime;
      setCurrentTime(time);
      setLocalTime(time);
      setDuration(audioRef.current.duration || 0);
    }
  };

  const handleEnded = () => {
    nextChapter();
  };

  const handleSliderChange = (value: number[]) => {
    setIsDragging(true);
    setLocalTime(value[0]);
  };

  const handleSliderCommit = (value: number[]) => {
    if (audioRef.current) {
      audioRef.current.currentTime = value[0];
      setCurrentTime(value[0]);
    }
    setIsDragging(false);
  };

  const formatTime = (seconds: number) => {
    if (!seconds || isNaN(seconds)) return "00:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  };

  if (!currentChapter) return null;

  return (
    <>
      <audio
        ref={audioRef}
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleEnded}
        onPause={() => setIsPlaying(false)}
        onPlay={() => setIsPlaying(true)}
      />

      {/* Mini Player / Full Player Container */}
      <div
        className={cn(
          "fixed left-0 right-0 bg-background/95 backdrop-blur border-t transition-all duration-300 ease-in-out z-[100]",
          isExpanded
            ? "top-0 bottom-0 h-screen flex flex-col"
            : "bottom-16 md:bottom-0 h-20"
        )}
      >
        {/* Full Screen Header */}
        {isExpanded && (
          <div className="flex items-center justify-between p-4 border-b">
            <Button variant="ghost" size="icon" onClick={toggleExpanded}>
              <Minimize2 className="h-6 w-6" />
            </Button>
            <span className="font-semibold text-lg">Now Playing</span>
            <Button variant="ghost" size="icon" onClick={toggleExpanded}>
              <X className="h-6 w-6" />
            </Button>
          </div>
        )}

        <div
          className={cn(
            "flex items-center px-4",
            isExpanded
              ? "flex-col flex-1 justify-center space-y-8 p-8"
              : "h-full justify-between"
          )}
        >
          {/* Track Info */}
          <div
            className={cn(
              "flex items-center space-x-4",
              isExpanded && "flex-col space-x-0 space-y-4 text-center"
            )}
          >
            <div
              className={cn(
                "bg-primary/10 rounded-md flex items-center justify-center",
                isExpanded ? "h-64 w-64" : "h-12 w-12"
              )}
            >
              <Volume2
                className={cn(
                  "text-primary",
                  isExpanded ? "h-24 w-24" : "h-6 w-6"
                )}
              />
            </div>
            <div className="overflow-hidden">
              <h3
                className={cn(
                  "font-semibold truncate",
                  isExpanded ? "text-2xl" : "text-sm"
                )}
              >
                {currentChapter.title}
              </h3>
              <p
                className={cn(
                  "text-muted-foreground truncate",
                  isExpanded ? "text-lg" : "text-xs"
                )}
              >
                Chapter {currentChapter.chapter_number}
              </p>
            </div>
          </div>

          {/* Controls */}
          <div
            className={cn(
              "flex flex-col items-center",
              isExpanded
                ? "w-full max-w-md space-y-6"
                : "flex-1 mx-4 hidden md:flex"
            )}
          >
            {/* Progress Bar (Desktop Mini or Full Screen) */}
            <div className="w-full flex items-center space-x-2">
              <span className="text-xs text-muted-foreground w-10 text-right">
                {formatTime(localTime)}
              </span>
              <Slider
                value={[localTime]}
                max={duration || 100}
                step={1}
                onValueChange={handleSliderChange}
                onValueCommit={handleSliderCommit}
                className="flex-1"
              />
              <span className="text-xs text-muted-foreground w-10">
                {formatTime(duration || 0)}
              </span>
            </div>

            {/* Main Controls */}
            <div className="flex items-center space-x-6 mt-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={prevChapter}
                className={isExpanded ? "h-12 w-12" : ""}
              >
                <SkipBack className={isExpanded ? "h-8 w-8" : "h-5 w-5"} />
              </Button>
              <Button
                size="icon"
                className={cn(
                  "rounded-full",
                  isExpanded ? "h-16 w-16" : "h-10 w-10"
                )}
                onClick={togglePlay}
              >
                {isPlaying ? (
                  <Pause className={isExpanded ? "h-8 w-8" : "h-5 w-5"} />
                ) : (
                  <Play
                    className={cn(isExpanded ? "h-8 w-8" : "h-5 w-5", "ml-1")}
                  />
                )}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={nextChapter}
                className={isExpanded ? "h-12 w-12" : ""}
              >
                <SkipForward className={isExpanded ? "h-8 w-8" : "h-5 w-5"} />
              </Button>
            </div>
          </div>

          {/* Mobile Mini Controls */}
          {!isExpanded && (
            <div className="flex items-center space-x-2 md:hidden">
              <Button variant="ghost" size="icon" onClick={togglePlay}>
                {isPlaying ? (
                  <Pause className="h-5 w-5" />
                ) : (
                  <Play className="h-5 w-5" />
                )}
              </Button>
              <Button variant="ghost" size="icon" onClick={toggleExpanded}>
                <Maximize2 className="h-5 w-5" />
              </Button>
            </div>
          )}

          {/* Desktop Extra Controls */}
          {!isExpanded && (
            <div className="hidden md:flex items-center space-x-2 w-32 justify-end">
              <Button variant="ghost" size="icon" onClick={toggleExpanded}>
                <Maximize2 className="h-5 w-5" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
