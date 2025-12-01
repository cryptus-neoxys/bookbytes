import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { Chapter } from "@/lib/api";

interface AudioState {
  currentChapter: Chapter | null;
  playlist: Chapter[];
  bookIsbn: string | null;
  isPlaying: boolean;
  currentIndex: number;
  currentTime: number;
  duration: number;
  volume: number;
  playbackRate: number;
  isExpanded: boolean;

  setPlaylist: (chapters: Chapter[], isbn: string) => void;
  playChapter: (index: number) => void;
  togglePlay: () => void;
  setIsPlaying: (isPlaying: boolean) => void;
  nextChapter: () => void;
  prevChapter: () => void;
  setCurrentTime: (time: number) => void;
  setDuration: (duration: number) => void;
  setVolume: (volume: number) => void;
  setPlaybackRate: (rate: number) => void;
  toggleExpanded: () => void;
  reset: () => void;
}

export const useAudioStore = create<AudioState>()(
  persist(
    (set, get) => ({
      currentChapter: null,
      playlist: [],
      bookIsbn: null,
      isPlaying: false,
      currentIndex: -1,
      currentTime: 0,
      duration: 0,
      volume: 1,
      playbackRate: 1.0,
      isExpanded: false,

      setPlaylist: (chapters, isbn) => {
        // If setting the same playlist, don't reset everything unless it's empty
        const { bookIsbn } = get();
        if (bookIsbn === isbn && chapters.length > 0) return;

        set({
          playlist: chapters,
          bookIsbn: isbn,
          currentIndex: -1,
          currentChapter: null,
          currentTime: 0,
          isPlaying: false,
        });
      },

      playChapter: (index) => {
        const { playlist } = get();
        if (index >= 0 && index < playlist.length) {
          set({
            currentIndex: index,
            currentChapter: playlist[index],
            isPlaying: true,
            currentTime: 0, // Reset time for new chapter
          });
        }
      },

      togglePlay: () => set((state) => ({ isPlaying: !state.isPlaying })),

      setIsPlaying: (isPlaying) => set({ isPlaying }),

      nextChapter: () => {
        const { currentIndex, playlist } = get();
        if (currentIndex < playlist.length - 1) {
          get().playChapter(currentIndex + 1);
        } else {
          // End of playlist
          set({ isPlaying: false, currentTime: 0 });
        }
      },

      prevChapter: () => {
        const { currentIndex, currentTime } = get();
        // If we are more than 3 seconds in, restart chapter
        if (currentTime > 3) {
          set({ currentTime: 0 });
          // We need to trigger a seek in the actual audio element,
          // which is handled by the component subscribing to this state
          return;
        }

        if (currentIndex > 0) {
          get().playChapter(currentIndex - 1);
        }
      },

      setCurrentTime: (time) => set({ currentTime: time }),
      setDuration: (duration) => set({ duration }),
      setVolume: (volume) => set({ volume }),
      setPlaybackRate: (rate) => set({ playbackRate: rate }),
      toggleExpanded: () => set((state) => ({ isExpanded: !state.isExpanded })),

      reset: () =>
        set({
          currentChapter: null,
          playlist: [],
          bookIsbn: null,
          isPlaying: false,
          currentIndex: -1,
          currentTime: 0,
          duration: 0,
        }),
    }),
    {
      name: "bookbytes-audio-storage",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Persist these fields
        currentChapter: state.currentChapter,
        playlist: state.playlist,
        bookIsbn: state.bookIsbn,
        currentIndex: state.currentIndex,
        currentTime: state.currentTime,
        volume: state.volume,
        playbackRate: state.playbackRate,
      }),
    }
  )
);
