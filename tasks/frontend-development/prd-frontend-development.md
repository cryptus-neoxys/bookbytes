# Product Requirements Document: BookBytes Frontend

## 1. Introduction/Overview

BookBytes is an application that converts physical non-fiction books into chapter-wise audio summaries. The goal of this frontend is to provide a user-friendly interface for users to process new books via ISBN, browse their library of summarized books, and listen to the audio summaries. This PRD outlines the requirements for the initial "Full Suite" MVP.

## 2. Goals

- **Seamless Book Processing:** Allow users to easily input an ISBN and trigger the backend processing pipeline.
- **Accessible Library:** Provide a clean, organized view of all processed books.
- **Immersive Listening:** Deliver a high-quality audio playback experience with continuous play and persistence across navigation.
- **Minimalist Design:** Ensure the UI is distraction-free, focusing on the content (book details and audio).

## 3. User Stories

- **As a user,** I want to enter a book's ISBN so that I can generate audio summaries for it.
- **As a user,** I want to see a list of all my processed books so that I can choose one to listen to.
- **As a user,** I want to view the chapters of a specific book so that I can select a specific topic to hear.
- **As a user,** I want the audio to continue playing when I browse other books so that my listening experience is uninterrupted.
- **As a user,** I want the next chapter to play automatically so that I don't have to manually interact with the app after every chapter.

## 4. Functional Requirements

### 4.1. Book Processing (Home/Dashboard)

1.  **ISBN Input:** A prominent input field to accept ISBN-10 or ISBN-13.
2.  **Process Action:** A "Process Book" button that triggers the `/api/process` endpoint.
3.  **Loading State:** Visual feedback (spinner/progress bar) while the book is being processed (fetching metadata, generating summaries, TTS).
4.  **Success/Error Feedback:** Clear notifications for successful processing or errors (e.g., "Book not found", "Processing failed").

### 4.2. Library View

1.  **Book List:** Display a grid or list of processed books.
2.  **Book Cards:** Each card should show the cover (if available/placeholder), title, author, and chapter count.
3.  **Navigation:** Clicking a book card navigates to the Book Details view.

### 4.3. Book Details View

1.  **Metadata:** Display full book details (Title, Author, Publish Date, Page Count).
2.  **Chapter List:** List all chapters with their titles and duration (if available) or word count.
3.  **Play Action:** Ability to start playing a specific chapter.

### 4.4. Audio Player

1.  **Persistent Player:** A fixed player bar at the bottom of the screen that remains visible while navigating.
2.  **Controls:** Play/Pause, Next Chapter, Previous Chapter, Volume control, Progress bar (scrubbing).
3.  **Continuous Playback:** Automatically play the next chapter when the current one ends.
4.  **Now Playing Info:** Display the current chapter title and book title.
5.  **Full Screen Mode:** Expandable player view (swipe up or tap) showing large cover art, full chapter list, and larger controls.
6.  **Gesture Controls:**
    - Swipe Left/Right on full screen player to skip chapters.
    - Double tap sides to seek +/- 10 seconds.
    - Swipe down to minimize player.
7.  **Background Audio:** Audio continues when the browser tab is backgrounded or the screen is locked.

## 5. Non-Goals (Out of Scope)

- **User Authentication:** The app will be single-user/local for this MVP.
- **Payment/Subscription:** No monetization features.
- **Social Features:** No sharing or commenting.

## 6. Design Considerations

- **Aesthetic:** Minimalist & Clean.
  - **Typography:** `Inter` or `Geist Sans` (Sans-serif). Large, legible headings. High contrast for readability.
  - **Color Palette:** Neutral monochrome (Slate/Zinc) with a single accent color (e.g., Deep Indigo or Teal) for primary actions.
  - **Whitespace:** Generous padding and margins to reduce cognitive load.
- **UI Components:**
  - **Cards:** Simple, flat or subtle shadow cards for book covers.
  - **Lists:** Clean, divided lists for chapters.
  - **Player:** Fixed bottom bar with a "glass" effect (backdrop-blur) or solid neutral background.
- **Responsiveness:** **Mobile-First Approach.**
  - **Touch Targets:** All interactive elements (buttons, list items) must have a minimum touch target size of 44x44px.
  - **Safe Areas:** Respect system safe areas (notch, home indicator) on mobile devices.
  - **Navigation:** Bottom navigation bar for primary actions (Home, Library, Player) on mobile; standard header on desktop.
  - **Player:** The mini-player must sit _above_ the bottom navigation bar on mobile to prevent accidental clicks.
- **Interactions:**
  - **Gestures:** Swipe-to-go-back, swipe-to-dismiss modals.
  - **Feedback:** Immediate visual feedback (ripple or scale) on touch.
  - **Transitions:** Smooth page transitions (slide-over for details views) to mimic native app feel.

## 7. Technical Considerations & Stack

### 7.1. Core Stack

- **Framework:** React 18+
- **Build Tool:** Vite
- **Language:** TypeScript
- **Styling:** Tailwind CSS

### 7.2. Key Libraries

- **UI Components:** `shadcn/ui` (built on Radix UI). Provides accessible, unstyled components that we can style with Tailwind for a custom minimalist look.
- **State Management:** `Zustand`. Used for:
  - Global Audio Player state (current track, playing status, playlist queue).
  - Persisting player state across route changes.
- **Data Fetching:** `TanStack Query` (React Query). Handles caching, loading states, and re-fetching for books and chapters.
- **Routing:** `React Router DOM` (v6).
- **Icons:** `Lucide React` (Clean, consistent SVG icons).
- **HTTP Client:** `Axios` (or native `fetch` via a wrapper).

### 7.3. Audio Implementation

- **Core:** Native HTML5 `<audio>` element.
- **State Sync:** The `<audio>` element will be wrapped in a provider or managed by the Zustand store to ensure it persists (does not unmount) when navigating between pages.
- **Events:** Listen for `ended` events to trigger the next chapter in the queue (Continuous Playback).
- **Media Session API:** Integrate `navigator.mediaSession` to support:
  - Lock screen controls (Play, Pause, Next, Prev).
  - Displaying metadata (Title, Artist, Artwork) in the system notification center/watch.
  - Handling hardware media keys.

## 8. Success Metrics

- **Successful Processing:** Users can successfully add books via ISBN without UI errors.
- **Playback Continuity:** Users can listen to multiple chapters in a row without manual intervention.
- **Navigation:** Users can browse the library while audio is playing.

## 9. Open Questions

- _None at this stage._
