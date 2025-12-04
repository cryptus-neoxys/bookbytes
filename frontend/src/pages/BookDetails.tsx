import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getChapters, getBook } from "@/lib/api";
import { PageContainer } from "@/components/layout/PageContainer";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, Play, Pause, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useAudioStore } from "@/store/useAudioStore";

export default function BookDetails() {
  const { isbn } = useParams<{ isbn: string }>();
  const {
    playChapter,
    setPlaylist,
    currentChapter,
    isPlaying,
    togglePlay,
    bookIsbn,
  } = useAudioStore();

  const {
    data: chaptersData,
    isLoading: isLoadingChapters,
    error: chaptersError,
  } = useQuery({
    queryKey: ["chapters", isbn],
    queryFn: () => getChapters(isbn!),
    enabled: !!isbn,
  });

  const {
    data: bookData,
    isLoading: isLoadingBook,
    error: bookError,
  } = useQuery({
    queryKey: ["book", isbn],
    queryFn: () => getBook(isbn!),
    enabled: !!isbn,
  });

  if (chaptersError || bookError) {
    return (
      <PageContainer>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            Failed to load book details. Please try again later.
          </AlertDescription>
        </Alert>
      </PageContainer>
    );
  }

  const handlePlay = (chapterIndex: number) => {
    if (chaptersData?.chapters) {
      // If playing the same book and chapter, just toggle
      const chapter = chaptersData.chapters[chapterIndex];
      const isCurrentChapter =
        currentChapter?.chapter_number === chapter.chapter_number &&
        bookIsbn === isbn;

      if (isCurrentChapter) {
        togglePlay();
      } else {
        setPlaylist(chaptersData.chapters, chaptersData.isbn);
        playChapter(chapterIndex);
      }
    }
  };

  const isLoading = isLoadingChapters || isLoadingBook;

  return (
    <PageContainer>
      {isLoading ? (
        <div className="space-y-6">
          <Skeleton className="h-12 w-3/4" />
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold">
              {bookData?.book.title || "Chapters"}
            </h1>
            <p className="text-muted-foreground">
              {bookData?.book.author} • {chaptersData?.count} Chapters available
            </p>
          </div>

          <div className="grid gap-4">
            {chaptersData?.chapters.map((chapter, index) => {
              const isCurrentChapter =
                currentChapter?.chapter_number === chapter.chapter_number &&
                bookIsbn === isbn;
              const isPlayingCurrent = isCurrentChapter && isPlaying;

              return (
                <Card
                  key={chapter.chapter_number}
                  className={cn(
                    "transition-colors",
                    isCurrentChapter
                      ? "border-primary bg-primary/5"
                      : "hover:bg-accent/50"
                  )}
                >
                  <CardContent className="p-4 flex items-center justify-between">
                    <div className="space-y-1 flex-1 mr-4">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-muted-foreground">
                          #{chapter.chapter_number}
                        </span>
                        <h3
                          className={cn(
                            "font-semibold leading-none tracking-tight",
                            isCurrentChapter && "text-primary"
                          )}
                        >
                          {chapter.title}
                        </h3>
                      </div>
                      <div className="flex items-center text-sm text-muted-foreground space-x-4">
                        {chapter.word_count && (
                          <span className="flex items-center">
                            <FileText className="mr-1 h-3 w-3" />
                            {chapter.word_count} words
                          </span>
                        )}
                        {/* Duration would be nice if we had it */}
                      </div>
                    </div>
                    <Button
                      size="icon"
                      variant={
                        isCurrentChapter
                          ? "default"
                          : chapter.has_audio
                          ? "secondary"
                          : "ghost"
                      }
                      disabled={!chapter.has_audio}
                      onClick={() => handlePlay(index)}
                    >
                      {isPlayingCurrent ? (
                        <Pause className="h-4 w-4" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </PageContainer>
  );
}
