"use client";

import React, { useEffect, useState } from "react";
import { apiClient, ModelMetaResponse } from "@cinematch/api-client";
import { aboutCopy } from "@/copy/about";
import { ShieldCheck, BarChart2, Zap, Database, Activity, CheckCircle2 } from "lucide-react";

export default function ModelReportTab() {
  const [meta, setMeta] = useState<ModelMetaResponse | null>(null);

  useEffect(() => {
    apiClient.getModelMeta().then((m) => setMeta(m)).catch(() => {});
  }, []);

  const benchmarkData = [
    {
      model: "Popularity Baseline",
      type: "Baseline",
      valNdcg: "0.0544",
      testNdcg: "0.0563",
      ci: "[0.048, 0.065]",
      recall: "0.0390",
      hitRate: "27.8%",
      novelty: "6.08",
      diversity: "0.852",
      badge: "Validated Global Benchmark",
      badgeColor: "bg-amber-950/40 border-amber-500/30 text-amber-400",
    },
    {
      model: "CineMatch Hybrid (v2)",
      type: "Production Hybrid",
      valNdcg: "0.0415",
      testNdcg: "0.0409",
      ci: "[0.033, 0.048]",
      recall: "0.0304",
      hitRate: "21.5%",
      novelty: "6.63",
      diversity: "0.853",
      badge: "Personalized Engine",
      badgeColor: "bg-emerald-950/40 border-emerald-500/30 text-emerald-400",
    },
    {
      model: "Explicit ALS (NumPy)",
      type: "Latent Factor CF",
      valNdcg: "0.0402",
      testNdcg: "0.0406",
      ci: "[0.033, 0.048]",
      recall: "0.0298",
      hitRate: "23.2%",
      novelty: "6.72",
      diversity: "0.851",
    },
    {
      model: "Item-kNN Collaborative",
      type: "Memory-Based CF",
      valNdcg: "0.0121",
      testNdcg: "0.0126",
      ci: "[0.008, 0.017]",
      recall: "0.0099",
      hitRate: "8.8%",
      novelty: "7.77",
      diversity: "0.778",
    },
    {
      model: "TF-IDF Content Vector",
      type: "Unsupervised Content",
      valNdcg: "0.0045",
      testNdcg: "0.0047",
      ci: "[0.002, 0.007]",
      recall: "0.0039",
      hitRate: "3.6%",
      novelty: "7.74",
      diversity: "0.840",
    },
  ];

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
                {meta?.dataset_fingerprint ? `Dataset: ${meta.dataset_fingerprint.slice(0, 8)}` : "Verified Split"}
              </span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight mt-1">
              {aboutCopy.modelReport.heading}
            </h2>
            <p className="text-xs text-zinc-400 mt-1 max-w-2xl">
              {aboutCopy.modelReport.protocolDesc}
            </p>
          </div>

          {meta?.quality_gate_selected_model && (
            <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/30 text-xs font-mono space-y-1">
              <span className="text-zinc-400 block text-[10px] uppercase tracking-wider">Active Strategy:</span>
              <span className="font-bold text-amber-400">{meta.quality_gate_selected_model}</span>
            </div>
          )}
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
            591 test users • 95% Bootstrap CI
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-zinc-900/60 text-zinc-400 border-b border-zinc-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Model Strategy</th>
                <th className="py-3 px-4 font-semibold">Type</th>
                <th className="py-3 px-4 font-semibold text-right">NDCG@10</th>
                <th className="py-3 px-4 font-semibold text-right">95% CI</th>
                <th className="py-3 px-4 font-semibold text-right">Recall@10</th>
                <th className="py-3 px-4 font-semibold text-right">Hit Rate</th>
                <th className="py-3 px-4 font-semibold text-right">Novelty</th>
                <th className="py-3 px-4 font-semibold text-right">Diversity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
              {benchmarkData.map((row, idx) => (
                <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 px-4 font-medium text-white flex items-center gap-2">
                    <span>{row.model}</span>
                    {row.badge && (
                      <span className={`px-2 py-0.5 rounded-full text-[10px] border ${row.badgeColor}`}>
                        {row.badge}
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-zinc-400">{row.type}</td>
                  <td className="py-3.5 px-4 text-right font-bold text-amber-400">{row.testNdcg}</td>
                  <td className="py-3.5 px-4 text-right text-zinc-500">{row.ci}</td>
                  <td className="py-3.5 px-4 text-right">{row.recall}</td>
                  <td className="py-3.5 px-4 text-right">{row.hitRate}</td>
                  <td className="py-3.5 px-4 text-right">{row.novelty}</td>
                  <td className="py-3.5 px-4 text-right">{row.diversity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
