import React from "react";
import { cn } from "@/lib/utils";

interface PageContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export const PageContainer = ({
  children,
  className,
  ...props
}: PageContainerProps) => {
  return (
    <div
      className={cn(
        "container mx-auto px-4 py-6 max-w-3xl pb-24 md:pb-6", // pb-24 for mobile nav + player space
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
