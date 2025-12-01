import { BookOpen } from "lucide-react";
import { Link } from "react-router-dom";

export const Navbar = () => {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 hidden md:block">
      <div className="container flex h-14 items-center max-w-3xl mx-auto px-4">
        <Link to="/" className="flex items-center space-x-2">
          <BookOpen className="h-6 w-6" />
          <span className="font-bold">BookBytes</span>
        </Link>
        <nav className="flex items-center space-x-6 text-sm font-medium ml-6">
          <Link
            to="/"
            className="transition-colors hover:text-foreground/80 text-foreground/60"
          >
            Home
          </Link>
          <Link
            to="/library"
            className="transition-colors hover:text-foreground/80 text-foreground/60"
          >
            Library
          </Link>
        </nav>
      </div>
    </header>
  );
};
