"use client";
import React, { useEffect, useState } from "react";
import { aboutCopy } from "@/copy/about";
import { BarChart2, ShieldCheck, Activity, Database, CheckCircle2 } from "lucide-react";

interface ModelMetric {
  mean: number;
  ci_lower: number;
  ci_upper: number;
}

interface ModelEvalItem {
  ndcg?: ModelMetric;
  recall?: ModelMetric;
  map?: ModelMetric;
  hit_rate?: ModelMetric;
  novelty?: ModelMetric;
  diversity?: ModelMetric;
  catalog_coverage?: number;
  n_evaluated_users?: number;
}

interface ColdStartCurveItem {
  ratings_count: number;
  ndcg_mean: number;
  hit_rate_mean: number;
}

interface AboutApiResponse {
  dataset: {
    name: string;
    citation: string;
    clean_ratings: number;
    clean_users: number;
    clean_movies: number;
    sparsity_pct: number;
    terms: string;
  };
  evaluation: {
    models?: Record<string, ModelEvalItem>;
    cold_start_curves?: Record<string, ColdStartCurveItem>;
    test_users?: number;
    test_ratings?: number;
  };
  active_strategy: {
    strategy: string;
    data?: {
      selected_model?: string;
      is_hybrid_superior?: boolean;
      validation_ndcg_hybrid?: number;
      best_single_model?: string;
      validation_ndcg_best_single?: number;
      rationale?: string;
    };
  };
  versions: Record<string, string>;
  licenses: Record<string, string>;
}

export default function ModelReportTab() {
  const [data, setData] = useState<AboutApiResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/about")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch /api/about");
        return res.json() as Promise<AboutApiResponse>;
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="p-12 text-center text-xs font-mono text-zinc-500">
        Generating model report from live evaluation artifacts...
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8 text-center text-xs font-mono text-red-400">
        Evaluation artifact not available.
      </div>
    );
  }

  const models = data.evaluation?.models || {};
  const activeStrategy = data.active_strategy?.strategy || "Popularity Baseline";
  const dataset = data.dataset;

  return (
    <div className="space-y-6 text-zinc-300">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-[#141417] border border-zinc-800 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-amber-500 uppercase tracking-widest">
                Statistical Benchmark Audit
              </span>
              <span className="text-zinc-600">•</span>
              <span className="text-xs text-emerald-400 font-mono">
                {dataset.clean_movies.toLocaleString()} Movies • {dataset.clean_users.toLocaleString()} Users
              </span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight mt-1">
              {aboutCopy.modelReport.heading}
            </h2>
            <p className="text-xs text-zinc-400 mt-1 max-w-2xl">
              {aboutCopy.modelReport.protocolDesc}
            </p>
          </div>

          <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/30 text-xs font-mono space-y-1">
            <span className="text-zinc-400 block text-[10px] uppercase tracking-wider">Active Strategy:</span>
            <span className="font-bold text-amber-400">{activeStrategy}</span>
          </div>
        </div>
      </div>

      {/* Benchmark Metric Table */}
      <div className="rounded-2xl bg-[#141417] border border-zinc-800 shadow-xl overflow-hidden">
        <div className="p-5 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white tracking-tight">
              Held-Out Test Set Ranking Results (@10)
            </h3>
          </div>
          <span className="text-[11px] font-mono text-zinc-500">
            {data.evaluation?.test_users ? `${data.evaluation.test_users} test users • ` : ""}95% Bootstrap CI
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-zinc-900/60 text-zinc-400 border-b border-zinc-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Model Strategy</th>
                <th className="py-3 px-4 font-semibold text-right">NDCG@10</th>
                <th className="py-3 px-4 font-semibold text-right">95% CI</th>
                <th className="py-3 px-4 font-semibold text-right">Recall@10</th>
                <th className="py-3 px-4 font-semibold text-right">Hit Rate</th>
                <th className="py-3 px-4 font-semibold text-right">Novelty</th>
                <th className="py-3 px-4 font-semibold text-right">Diversity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
              {Object.entries(models).map(([name, m]) => {
                const isWinner = name === activeStrategy;
                return (
                  <tr key={name} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3.5 px-4 font-medium text-white flex items-center gap-2">
                      <span>{name}</span>
                      {isWinner && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] border bg-emerald-950/40 border-emerald-500/30 text-emerald-400">
                          Production Serving
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right font-bold text-amber-400">
                      {m.ndcg?.mean.toFixed(4) || "—"}
                    </td>
                    <td className="py-3.5 px-4 text-right text-zinc-500">
                      {m.ndcg ? `[${m.ndcg.ci_lower.toFixed(3)}, ${m.ndcg.ci_upper.toFixed(3)}]` : "—"}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {m.recall?.mean.toFixed(4) || "—"}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {m.hit_rate ? `${(m.hit_rate.mean * 100).toFixed(1)}%` : "—"}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {m.novelty?.mean.toFixed(2) || "—"}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      {m.diversity?.mean.toFixed(3) || "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cold-Start Progression Cards */}
      {data.evaluation?.cold_start_curves && (
        <div className="rounded-2xl bg-[#141417] border border-zinc-800 p-5 shadow-xl space-y-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white tracking-tight">
              Cold-Start Progression Curve
            </h3>
          </div>
          <p className="text-xs text-zinc-400">{aboutCopy.modelReport.coldStartNote}</p>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
            {Object.entries(data.evaluation.cold_start_curves).map(([key, item]) => (
              <div key={key} className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80 text-center font-mono">
                <span className="text-[10px] text-zinc-500 uppercase block">{item.ratings_count} Ratings</span>
                <span className="text-sm font-bold text-amber-400 block mt-1">
                  NDCG: {item.ndcg_mean.toFixed(3)}
                </span>
                <span className="text-[10px] text-emerald-400 block mt-0.5">
                  Hit: {(item.hit_rate_mean * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
