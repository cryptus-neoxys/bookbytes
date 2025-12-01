import { Home, Library } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

export const BottomNav = () => {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background/95 backdrop-blur md:hidden">
      <div className="flex items-center justify-around h-16">
        <Link
          to="/"
          className={cn(
            "flex flex-col items-center justify-center w-full h-full space-y-1",
            isActive("/") ? "text-primary" : "text-muted-foreground"
          )}
        >
          <Home className="h-5 w-5" />
          <span className="text-xs font-medium">Home</span>
        </Link>
        <Link
          to="/library"
          className={cn(
            "flex flex-col items-center justify-center w-full h-full space-y-1",
            isActive("/library") ? "text-primary" : "text-muted-foreground"
          )}
        >
          <Library className="h-5 w-5" />
          <span className="text-xs font-medium">Library</span>
        </Link>
      </div>
    </div>
  );
};
