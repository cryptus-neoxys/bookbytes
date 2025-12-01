import { useQuery } from "@tanstack/react-query";
import { getBooks } from "@/lib/api";
import { PageContainer } from "@/components/layout/PageContainer";
import { BookCard } from "@/components/ui/book-card";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export default function Library() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["books"],
    queryFn: getBooks,
  });

  if (error) {
    return (
      <PageContainer>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            Failed to load books. Please try again later.
          </AlertDescription>
        </Alert>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Your Library</h1>
        <Button asChild size="sm">
          <Link to="/">Process New Book</Link>
        </Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="space-y-3">
              <Skeleton className="h-[125px] w-full rounded-xl" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-[250px]" />
                <Skeleton className="h-4 w-[200px]" />
              </div>
            </div>
          ))}
        </div>
      ) : data?.books.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground mb-4">No books processed yet.</p>
          <Button asChild>
            <Link to="/">Get Started</Link>
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {data?.books.map((book) => (
            <BookCard key={book.isbn} book={book} />
          ))}
        </div>
      )}
    </PageContainer>
  );
}
