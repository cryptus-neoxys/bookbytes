import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";
import { BottomNav } from "./BottomNav";
import { Toaster } from "@/components/ui/toaster";
import { AudioPlayer } from "@/components/player/AudioPlayer";

export const Layout = () => {
  return (
    <div className="min-h-screen bg-background font-sans antialiased pb-20 md:pb-0">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <BottomNav />
      <AudioPlayer />
      <Toaster />
    </div>
  );
};
