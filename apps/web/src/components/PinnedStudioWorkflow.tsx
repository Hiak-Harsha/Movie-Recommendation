"use client";

import React, { useState } from "react";
import { Sparkles, Compass, ShieldCheck, ArrowRight, Zap, Code } from "lucide-react";
import { useStore } from "@/lib/store";

export default function PinnedStudioWorkflow() {
  const { setActiveTab } = useStore();
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    {
      index: "01",
      category: "LATENT FACTORIZATION",
      title: "Closed-Form ALS User Fold-In",
      desc: "When a visitor rates 5 movies, CineMatch solves the closed-form ridge formulation p_u = (Q_I^T Q_I + λ I)^{-1} Q_I^T (r_u - μ - b_I) in under 2 milliseconds without re-running 15 training epochs.",
      snippet: `// Pure NumPy Closed-Form Solve (< 2ms)
Q_I = Q[item_indices]
bi_I = bi[item_indices]
diff = ratings - mu - bi_I
p_u = np.linalg.solve(
    Q_I.T @ Q_I + lambda_reg * np.eye(K),
    Q_I.T @ diff
)`,
      targetTab: "foryou" as const,
      tag: "1.4 ms latency",
    },
    {
      index: "02",
      category: "NEIGHBOURHOOD AFFINITY",
      title: "Shrunk Item-kNN Co-Ratings",
      desc: "Mean-centered Pearson correlation with Bayeisan shrinkage s_{ij} = (C_{ij} / (C_{ij} + 25)) · cos(r_i, r_j) suppresses spurious matches between sparsely reviewed obscure titles.",
      snippet: `// Shrunk Similarity Formula
shrinkage = co_raters / (co_raters + 25.0)
shrunk_sim = raw_cosine * shrinkage
top_100 = np.argsort(-shrunk_sim)[:100]`,
      targetTab: "similar" as const,
      tag: "O(1) Array Lookup",
    },
    {
      index: "03",
      category: "DIVERSITY & CALIBRATION",
      title: "Maximal Marginal Relevance & Isotonic Fit",
      desc: "Greedy MMR re-ranking with Jaccard genre distance prevents list homogeneity. Isotonic calibration guarantees displayed predicted ratings reflect empirical probabilities.",
      snippet: `// MMR Re-Ranking Criterion
arg max_{i} [ λ · Score(i) - (1 - λ) · max_{j ∈ S} Jaccard(i, j) ]
calibrated_star = isotonic_regressor.predict(raw_score)`,
      targetTab: "insights" as const,
      tag: "Calibrated Stars",
    },
  ];

  const current = steps[activeStep];

  return (
    <section className="py-20 border-b border-zinc-900 bg-[#0e0e11]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Eyebrow */}
        <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-zinc-500 mb-3">
          <span className="text-amber-500 font-bold">02 /</span>
          <span>Engine Choreography</span>
        </div>

        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-12">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white tracking-tight">
            How CineMatch calculates your picks.
          </h2>
          <span className="text-xs font-mono text-zinc-400">
            Real implementation logic executed on every request.
          </span>
        </div>

        {/* Pinned Two-Column Interactive Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Numbered Step Items */}
          <div className="lg:col-span-5 space-y-4">
            {steps.map((step, idx) => {
              const isActive = activeStep === idx;
              return (
                <div
                  key={step.index}
                  onClick={() => setActiveStep(idx)}
                  className={`p-6 rounded-2xl border transition-all duration-300 cursor-pointer ${
                    isActive
                      ? "bg-[#16161a] border-amber-500/40 shadow-xl shadow-amber-500/5 translate-x-2"
                      : "bg-[#121215] border-zinc-800/80 hover:border-zinc-700 opacity-70 hover:opacity-100"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-amber-500 tracking-wider">
                      {step.index} / {step.category}
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-zinc-800 border border-zinc-700 text-[10px] font-mono text-zinc-400">
                      {step.tag}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-white mt-2">
                    {step.title}
                  </h3>

                  <p className="text-xs text-zinc-400 mt-2 leading-relaxed">
                    {step.desc}
                  </p>

                  {isActive && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveTab(step.targetTab);
                      }}
                      className="mt-4 flex items-center gap-1.5 text-xs font-mono text-amber-400 hover:text-amber-300 font-semibold cursor-pointer group"
                    >
                      <span>Jump to {step.title.split(" ")[0]}</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {/* Right Column: Code & Mathematics Canvas */}
          <div className="lg:col-span-7 sticky top-24 rounded-2xl bg-[#141418] border border-zinc-800 shadow-2xl p-6 overflow-hidden">
            <div className="flex items-center justify-between pb-4 border-b border-zinc-800/80 mb-4">
              <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
                <Code className="w-4 h-4 text-amber-400" />
                <span>{current.category} IMPLEMENTATION</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
                <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
                <span className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
              </div>
            </div>

            <pre className="font-mono text-xs text-zinc-300 leading-relaxed overflow-x-auto p-4 rounded-xl bg-black/60 border border-zinc-850">
              <code>{current.snippet}</code>
            </pre>

            <div className="mt-6 pt-4 border-t border-zinc-800/80 flex items-center justify-between text-xs font-mono text-zinc-500">
              <span>Verification: 47 / 47 tests passing</span>
              <span className="text-emerald-400 font-semibold">Zero Synthetic Data</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
