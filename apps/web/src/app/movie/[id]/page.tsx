"use client";
import React, { useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { useAppStore } from "@/core/store";
import { DetailOverlay } from "@/modules/detail";

export default function MovieDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const resolvedParams = use(params);
  const movieId = parseInt(resolvedParams.id, 10);
  const setSelectedMovieId = useAppStore((s) => s.setSelectedMovieId);
  const selectedMovieId = useAppStore((s) => s.selectedMovieId);

  useEffect(() => {
    if (!isNaN(movieId)) {
      setSelectedMovieId(movieId);
    }
  }, [movieId, setSelectedMovieId]);

  useEffect(() => {
    // If closed, route back to home
    if (selectedMovieId === null) {
      router.push("/");
    }
  }, [selectedMovieId, router]);

  return <DetailOverlay />;
}
