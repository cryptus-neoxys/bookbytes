import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { processBook } from "@/lib/api";
import { PageContainer } from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { Loader2, BookOpen } from "lucide-react";

export default function Home() {
  const [isbn, setIsbn] = useState("");
  const navigate = useNavigate();
  const { toast } = useToast();

  const processMutation = useMutation({
    mutationFn: processBook,
    onSuccess: (data) => {
      toast({
        title: "Book Processed Successfully",
        description: `Processed "${data.book.title}" with ${data.chapters_processed} chapters.`,
      });
      navigate("/library");
    },
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onError: (error: any) => {
      toast({
        variant: "destructive",
        title: "Processing Failed",
        description:
          error.response?.data?.message ||
          error.message ||
          "An unexpected error occurred.",
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isbn.trim()) return;
    processMutation.mutate(isbn);
  };

  return (
    <PageContainer className="flex flex-col items-center justify-center min-h-[80vh]">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center space-y-2">
          <div className="flex justify-center mb-4">
            <div className="p-4 bg-primary/10 rounded-full">
              <BookOpen className="h-12 w-12 text-primary" />
            </div>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">BookBytes</h1>
          <p className="text-muted-foreground">
            Turn your physical books into audio summaries instantly.
          </p>
        </div>

        <Card className="border-border/50 shadow-lg">
          <CardHeader>
            <CardTitle>Process New Book</CardTitle>
            <CardDescription>
              Enter the ISBN-10 or ISBN-13 of the book you want to convert.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Input
                  placeholder="e.g. 978-0735211292"
                  value={isbn}
                  onChange={(e) => setIsbn(e.target.value)}
                  disabled={processMutation.isPending}
                  className="text-lg h-12"
                />
              </div>
              <Button
                type="submit"
                className="w-full h-12 text-lg"
                disabled={!isbn.trim() || processMutation.isPending}
              >
                {processMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  "Generate Audio Summary"
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="text-center text-sm text-muted-foreground">
          <p>Processing may take 1-2 minutes depending on the book length.</p>
        </div>
      </div>
    </PageContainer>
  );
}
