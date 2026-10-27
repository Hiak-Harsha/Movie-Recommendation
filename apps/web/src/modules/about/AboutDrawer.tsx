"use client";

import React, { useState } from "react";
import { useAppStore } from "@/core/store";
import { aboutCopy } from "@/copy/about";
import ModelReportTab from "./ModelReportTab";
import { X, BookOpen, Cpu, Award, Shield, BarChart3, Download, Trash2, Key } from "lucide-react";

export default function AboutDrawer() {
  const isAboutOpen = useAppStore((s) => s.isAboutOpen);
  const setIsAboutOpen = useAppStore((s) => s.setIsAboutOpen);
  const aboutTab = useAppStore((s) => s.aboutTab);
  const setAboutTab = useAppStore((s) => s.setAboutTab);
  const setToast = useAppStore((s) => s.setToast);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  if (!isAboutOpen) return null;

  const handleExportData = () => {
    window.open(`/api/me/export`, "_blank");
  };

  const handleEraseData = async () => {
    if (!window.confirm(aboutCopy.terms.eraseConfirm)) return;
    try {
      const res = await fetch("/api/me", { method: "DELETE" });
      if (res.ok) {
        setToast({ message: "All personal data erased from session." });
        setIsAboutOpen(false);
        window.location.reload();
      }
    } catch (e: any) {
      setToast({ message: "Failed to erase data: " + e.message });
    }
  };

  const tabButtons = [
    { id: "howToUse", label: aboutCopy.tabs.howToUse, icon: BookOpen },
    { id: "howItWorks", label: aboutCopy.tabs.howItWorks, icon: Cpu },
    { id: "dataCredits", label: aboutCopy.tabs.dataCredits, icon: Award },
    { id: "terms", label: aboutCopy.tabs.terms, icon: Shield },
    { id: "modelReport", label: aboutCopy.tabs.modelReport, icon: BarChart3 },
  ];

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/80 backdrop-blur-md">
      <div
        className="relative w-full max-w-2xl h-full bg-[#121316] border-l border-zinc-800 shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">{aboutCopy.title}</h2>
            <p className="text-xs text-zinc-400 mt-0.5">{aboutCopy.subtitle}</p>
          </div>
          <button
            onClick={() => setIsAboutOpen(false)}
            className="p-2 rounded-full bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors cursor-pointer"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1 p-2 bg-[#0e0e11] border-b border-zinc-800 overflow-x-auto">
          {tabButtons.map((tb) => {
            const Icon = tb.icon;
            const active = (aboutTab || "howToUse") === tb.id;
            return (
              <button
                key={tb.id}
                onClick={() => setAboutTab(tb.id as any)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all cursor-pointer ${
                  active
                    ? "bg-amber-500 text-black font-semibold shadow-md"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-white/5"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tb.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* TAB 1: How to use */}
          {aboutTab === "howToUse" && (
            <div className="space-y-6 text-zinc-300">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {aboutCopy.howToUse.steps.map((st, i) => (
                  <div key={i} className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-2">
                    <span className="font-mono text-xs font-bold text-amber-500">{st.number}</span>
                    <h3 className="text-sm font-semibold text-white">{st.title}</h3>
                    <p className="text-xs text-zinc-400 leading-relaxed">{st.desc}</p>
                  </div>
                ))}
              </div>

              {/* Shortcuts Table */}
              <div className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-white uppercase tracking-wider font-mono">
                  <Key className="w-4 h-4 text-amber-400" />
                  <span>Keyboard Navigation</span>
                </div>
                <div className="divide-y divide-zinc-800/80 text-xs font-mono">
                  {aboutCopy.howToUse.shortcuts.map((sc, i) => (
                    <div key={i} className="py-2 flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded bg-black/60 border border-zinc-700 text-amber-400 font-bold">
                        {sc.key}
                      </span>
                      <span className="text-zinc-300 font-sans">{sc.action}</span>
                    </div>
                  ))}
                </div>
              </div>

              <p className="text-xs text-zinc-500 italic p-3 rounded-lg bg-zinc-900/30 border border-zinc-850">
                {aboutCopy.howToUse.tips}
              </p>
            </div>
          )}

          {/* TAB 2: How it works */}
          {aboutTab === "howItWorks" && (
            <div className="space-y-6 text-zinc-300">
              <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800">
                <h3 className="text-sm font-bold text-white mb-2">Plain Language Overview</h3>
                <p className="text-sm text-zinc-300 leading-relaxed">{aboutCopy.howItWorks.summary}</p>
              </div>

              <div className="space-y-3">
                <button
                  onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                  className="flex items-center justify-between w-full p-4 rounded-xl bg-zinc-900 border border-zinc-800 text-xs font-bold text-amber-400 hover:text-amber-300 uppercase tracking-wider font-mono cursor-pointer"
                >
                  <span>{aboutCopy.howItWorks.technicalTitle}</span>
                  <span>{showTechnicalDetails ? "−" : "+"}</span>
                </button>

                {showTechnicalDetails && (
                  <div className="space-y-3 p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/80 text-xs space-y-4">
                    {aboutCopy.howItWorks.technicalDetails.map((td, i) => (
                      <div key={i} className="space-y-1">
                        <h4 className="font-semibold text-white font-mono">{td.component}</h4>
                        <p className="text-zinc-400 leading-relaxed">{td.detail}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: Data & Credits */}
          {aboutTab === "dataCredits" && (
            <div className="space-y-6 text-zinc-300">
              <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-3">
                <h3 className="text-sm font-bold text-white">MovieLens Citation</h3>
                <p className="text-xs font-mono text-amber-400/90 leading-relaxed bg-black/40 p-3 rounded-lg border border-zinc-800">
                  {aboutCopy.dataCredits.movieLensCitation}
                </p>
                <p className="text-xs text-zinc-400">{aboutCopy.dataCredits.licenseNotice}</p>
              </div>

              <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-2">
                <h3 className="text-sm font-bold text-white">The Movie Database (TMDB)</h3>
                <p className="text-xs text-zinc-400 leading-relaxed">{aboutCopy.dataCredits.tmdbAttribution}</p>
              </div>
            </div>
          )}

          {/* TAB 4: Terms & Privacy */}
          {aboutTab === "terms" && (
            <div className="space-y-6 text-zinc-300">
              <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-3">
                <h3 className="text-sm font-bold text-white">Privacy & Scope</h3>
                <p className="text-xs text-zinc-400 leading-relaxed">{aboutCopy.terms.purpose}</p>
                <p className="text-xs text-zinc-400 leading-relaxed">{aboutCopy.terms.cookieNotice}</p>
              </div>

              <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-4">
                <h3 className="text-sm font-bold text-white">{aboutCopy.terms.exportHeading}</h3>
                <p className="text-xs text-zinc-400">{aboutCopy.terms.exportDesc}</p>
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={handleExportData}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-white transition-colors cursor-pointer"
                  >
                    <Download className="w-4 h-4 text-amber-400" />
                    <span>{aboutCopy.terms.exportButton}</span>
                  </button>

                  <button
                    onClick={handleEraseData}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-950/40 hover:bg-red-950/80 border border-red-500/40 text-xs font-semibold text-red-300 transition-colors cursor-pointer"
                  >
                    <Trash2 className="w-4 h-4 text-red-400" />
                    <span>{aboutCopy.terms.eraseButton}</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: Model Report */}
          {aboutTab === "modelReport" && <ModelReportTab />}
        </div>
      </div>
    </div>
  );
}
