## Relevant Files

- `frontend/src/App.tsx` - Main application component and routing setup.
- `frontend/src/store/useAudioStore.ts` - Zustand store for global audio state management.
- `frontend/src/lib/api.ts` - Axios instance and API methods for backend communication.
- `frontend/src/components/layout/Layout.tsx` - Main layout wrapper handling mobile/desktop navigation and persistent player.
- `frontend/src/components/player/AudioPlayer.tsx` - Logic controller for the HTML5 audio element.
- `frontend/src/components/player/MiniPlayer.tsx` - Persistent bottom player bar.
- `frontend/src/components/player/FullScreenPlayer.tsx` - Expanded mobile player with gesture controls.
- `frontend/src/pages/Home.tsx` - Dashboard for processing new books.
- `frontend/src/pages/Library.tsx` - Grid view of processed books.
- `frontend/src/pages/BookDetails.tsx` - Chapter list and book metadata.

### Notes

- The frontend will be initialized in a `frontend` directory within the root.
- Ensure the Flask backend is running on port 5000 for API calls.
- Proxy configuration in `vite.config.ts` will be needed to avoid CORS issues during development.
- Use bun package manager

## Instructions for Completing Tasks

**IMPORTANT:** As you complete each task, you must check it off in this markdown file by changing `- [ ]` to `- [x]`. This helps track progress and ensures you don't skip any steps.

Example:

- `- [ ] 1.1 Read file` → `- [x] 1.1 Read file` (after completing)

Update the file after completing each sub-task, not just after completing an entire parent task.

## Tasks

- [x] 0.0 Create feature branch

  - [x] 0.1 Create and checkout a new branch `feature/frontend-mvp`

- [ ] 1.0 Initialize Project & Infrastructure

  - [x] 1.1 Create new Vite + React + TypeScript project in `frontend` directory
  - [x] 1.2 Install and configure Tailwind CSS (including `tailwind.config.js` with custom colors/fonts)
  - [x] 1.3 Install core dependencies: `axios`, `zustand`, `@tanstack/react-query`, `react-router-dom`, `lucide-react`, `clsx`, `tailwind-merge`
  - [x] 1.4 Initialize `shadcn/ui` and add essential components (Button, Card, Input, Slider, Toast, Skeleton)
  - [x] 1.5 Configure `vite.config.ts` with API proxy to `http://localhost:5000`
  - [x] 1.6 Setup project structure (`components`, `pages`, `hooks`, `store`, `lib`)

- [x] 2.0 Implement Core UI Components & Layout

  - [x] 2.1 Create `Layout` component with `Outlet` and placeholder for Player
  - [x] 2.2 Implement `Navbar` (Desktop) and `BottomNav` (Mobile)
  - [x] 2.3 Define global styles and typography in `index.css` (Inter/Geist font)
  - [x] 2.4 Create reusable `PageContainer` component for consistent padding/safe-areas

- [x] 3.0 Implement Book Processing & Library Features

  - [x] 3.1 Create `lib/api.ts` with Axios instance and typed API functions (`processBook`, `getBooks`, `getChapters`)
  - [x] 3.2 Implement `Home` page with ISBN Input form and loading state
  - [x] 3.3 Implement `Library` page fetching books via React Query and displaying `BookCard` grid
  - [x] 3.4 Implement `BookDetails` page fetching chapters and displaying metadata
  - [x] 3.5 Add error handling (Toasts) for API failures

- [ ] 4.0 Implement Audio Player & Playback Logic

  - [x] 4.1 Create `useAudioStore` with Zustand (playlist management, playback state, persistence)Playing`, `progress`, `isExpanded`
  - [x] 4.2 Implement `AudioPlayer` component (logic-only) to handle `<audio>` events (`onTimeUpdate`, `onEnded`)
  - [x] 4.3 Implement `MiniPlayer` component (fixed bottom bar)
  - [x] 4.4 Implement `FullScreenPlayer` component (modal/overlay) with large cover and controls
  - [x] 4.5 Implement "Continuous Playback" logic (auto-play next chapter on end)
  - [x] 4.6 Integrate `AudioPlayer` into `Layout` so it persists across navigation

- [ ] 5.0 Polish & Mobile Optimization
  - [ ] 5.1 Implement `navigator.mediaSession` API for lock screen controls
  - [ ] 5.2 Add gesture controls to `FullScreenPlayer` (Swipe down to minimize, Swipe L/R to skip)
  - [ ] 5.3 Verify touch targets (min 44px) and mobile safe area padding
  - [ ] 5.4 Add skeleton loading states for Library and Details pages
