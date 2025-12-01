import { Link } from "react-router-dom";
import type { Book } from "@/lib/api";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BookOpen, Calendar, FileText } from "lucide-react";

interface BookCardProps {
  book: Book;
}

export function BookCard({ book }: BookCardProps) {
  return (
    <Card className="flex flex-col h-full hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <CardTitle className="line-clamp-2 text-lg leading-tight">
          {book.title}
        </CardTitle>
        <p className="text-sm text-muted-foreground line-clamp-1">
          {book.author}
        </p>
      </CardHeader>
      <CardContent className="flex-1 pb-2">
        <div className="flex flex-col space-y-2 text-sm text-muted-foreground">
          <div className="flex items-center">
            <BookOpen className="mr-2 h-4 w-4" />
            <span>{book.chapter_count || 0} Chapters</span>
          </div>
          {book.pages && (
            <div className="flex items-center">
              <FileText className="mr-2 h-4 w-4" />
              <span>{book.pages} Pages</span>
            </div>
          )}
          {book.publish_date && (
            <div className="flex items-center">
              <Calendar className="mr-2 h-4 w-4" />
              <span>{book.publish_date}</span>
            </div>
          )}
        </div>
      </CardContent>
      <CardFooter className="pt-2">
        <Button asChild className="w-full" variant="secondary">
          <Link to={`/book/${book.isbn}`}>View Chapters</Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
