import React from "react";

interface ProceduralPosterProps {
  movieId: number;
  title: string;
  year?: number | null;
  genres?: string[];
  className?: string;
}

// Pseudo-random deterministic hash from integer seed
function seededRandom(seed: number) {
  const x = Math.sin(seed++) * 10000;
  return x - Math.floor(x);
}

export const ProceduralPoster: React.FC<ProceduralPosterProps> = ({
  movieId,
  title,
  year,
  genres = [],
  className = "",
}) => {
  const primaryGenre = (genres[0] || "Drama").toLowerCase();
  const seed = movieId || 1;
  const rand1 = seededRandom(seed);
  const rand2 = seededRandom(seed + 1);

  // Auto-fit font size based on title length (never overflow, handles 40-char words)
  const len = title.length;
  let titleFontSize = 24;
  if (len > 30) titleFontSize = 14;
  else if (len > 20) titleFontSize = 16;
  else if (len > 12) titleFontSize = 19;
  else titleFontSize = 22;

  // Background and accent palettes by genre
  const palettes: Record<string, { bg: string; accent: string; sec: string }> = {
    "sci-fi": { bg: "#060914", accent: "#38bdf8", sec: "#1e1b4b" },
    horror: { bg: "#090406", accent: "#e11d48", sec: "#1c0a10" },
    western: { bg: "#160d06", accent: "#f59e0b", sec: "#3b1e08" },
    "film-noir": { bg: "#08080a", accent: "#f3f4f6", sec: "#262626" },
    romance: { bg: "#13080e", accent: "#f43f5e", sec: "#4c0519" },
    animation: { bg: "#08131d", accent: "#06b6d4", sec: "#f97316" },
    war: { bg: "#0d0f0c", accent: "#84cc16", sec: "#272a24" },
    crime: { bg: "#0a0a0c", accent: "#eab308", sec: "#1f1d13" },
    musical: { bg: "#11091a", accent: "#c084fc", sec: "#3b0764" },
    documentary: { bg: "#0c0d10", accent: "#a1a1aa", sec: "#18181b" },
    comedy: { bg: "#120e06", accent: "#facc15", sec: "#382405" },
    drama: { bg: "#09090b", accent: "#f5a524", sec: "#1c1917" },
    fantasy: { bg: "#060b17", accent: "#818cf8", sec: "#172554" },
    thriller: { bg: "#070b0e", accent: "#10b981", sec: "#064e3b" },
    adventure: { bg: "#07120e", accent: "#14b8a6", sec: "#042f2e" },
    mystery: { bg: "#0d0816", accent: "#a855f7", sec: "#2e1065" },
    children: { bg: "#091218", accent: "#38bdf8", sec: "#f472b6" },
  };

  const pal = palettes[primaryGenre] || palettes["drama"];

  // Render genre composition
  const renderComposition = () => {
    switch (primaryGenre) {
      case "sci-fi":
        return (
          <>
            <line x1="0" y1="260" x2="300" y2="260" stroke={pal.accent} strokeWidth="1" opacity="0.4" />
            <line x1="0" y1="285" x2="300" y2="285" stroke={pal.accent} strokeWidth="0.8" opacity="0.3" />
            <line x1="0" y1="315" x2="300" y2="315" stroke={pal.accent} strokeWidth="0.5" opacity="0.2" />
            <circle cx="150" cy="180" r="55" fill="none" stroke={pal.accent} strokeWidth="1.5" opacity="0.85" />
            <ellipse cx="150" cy="180" rx="85" ry="16" fill="none" stroke={pal.accent} strokeWidth="1" opacity="0.5" transform="rotate(-15 150 180)" />
          </>
        );
      case "horror":
        return (
          <>
            <radialGradient id={`hg_${seed}`} cx="50%" cy="40%" r="55%">
              <stop offset="0%" stopColor={pal.accent} stopOpacity="0.25" />
              <stop offset="100%" stopColor="#000000" stopOpacity="0.95" />
            </radialGradient>
            <rect x="0" y="0" width="300" height="450" fill={`url(#hg_${seed})`} />
            <line x1="120" y1="80" x2="125" y2="300" stroke={pal.accent} strokeWidth="1.5" opacity="0.4" />
            <line x1="150" y1="60" x2="148" y2="320" stroke={pal.accent} strokeWidth="2.5" opacity="0.6" />
            <line x1="180" y1="90" x2="175" y2="300" stroke={pal.accent} strokeWidth="1.5" opacity="0.4" />
          </>
        );
      case "western":
        return (
          <>
            <circle cx="150" cy="220" r="60" fill={pal.accent} opacity="0.3" />
            <path d="M0 320 Q 80 270 170 310 T 300 300 L 300 450 L 0 450 Z" fill={pal.sec} opacity="0.8" />
            <path d="M0 350 Q 120 310 210 340 T 300 330 L 300 450 L 0 450 Z" fill="#0b0b0c" opacity="0.9" />
          </>
        );
      case "film-noir":
        return (
          <>
            <polygon points="150,0 240,450 60,450" fill={pal.accent} opacity="0.12" />
            {[...Array(6)].map((_, i) => (
              <line key={i} x1="0" y1={120 + i * 28} x2="300" y2={120 + i * 28} stroke="#ffffff" strokeWidth="2" opacity="0.2" />
            ))}
          </>
        );
      case "romance":
        return (
          <>
            <circle cx="130" cy="200" r="65" fill={pal.accent} opacity="0.2" />
            <circle cx="170" cy="220" r="65" fill={pal.sec} opacity="0.4" />
          </>
        );
      case "animation":
        return (
          <>
            <circle cx="110" cy="180" r="45" fill={pal.accent} opacity="0.4" />
            <rect x="150" y="160" width="80" height="80" rx="16" fill={pal.sec} opacity="0.5" transform="rotate(25 190 200)" />
          </>
        );
      case "war":
        return (
          <>
            <path d="M0 240 L 60 210 L 140 250 L 220 200 L 300 230 L 300 450 L 0 450 Z" fill={pal.sec} opacity="0.7" />
            <path d="M0 290 L 90 260 L 180 300 L 250 270 L 300 290 L 300 450 L 0 450 Z" fill="#0b0b0c" opacity="0.9" />
          </>
        );
      case "crime":
        return (
          <>
            <polygon points="-20,180 320,240 320,280 -20,220" fill={pal.accent} opacity="0.25" />
            <polygon points="-20,270 320,330 320,350 -20,290" fill={pal.sec} opacity="0.4" />
          </>
        );
      default:
        // Drama & default: split-tone gradient with solitary geometric focal point
        return (
          <>
            <circle cx="150" cy="200" r={40 + rand1 * 30} fill="none" stroke={pal.accent} strokeWidth="1.5" opacity="0.6" />
            <rect x="130" y="180" width="40" height="40" fill={pal.accent} opacity="0.15" transform={`rotate(${rand2 * 45} 150 200)`} />
          </>
        );
    }
  };

  return (
    <svg
      viewBox="0 0 300 450"
      preserveAspectRatio="xMidYMid slice"
      className={`w-full h-full select-none ${className}`}
      role="img"
      aria-label={`${title} (${year || "film"})`}
    >
      <defs>
        {/* Film grain pattern */}
        <filter id={`grain_${seed}`} x="0%" y="0%" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" result="noise" />
          <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.07 0" />
          <feComposite in2="SourceGraphic" in="glitch" operator="arithmetic" k1="0" k2="1" k3="1" k4="0" />
        </filter>
        <linearGradient id={`bg_grad_${seed}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={pal.bg} />
          <stop offset="55%" stopColor={pal.sec} stopOpacity="0.4" />
          <stop offset="100%" stopColor="#050507" />
        </linearGradient>
      </defs>

      {/* Background Poster Canvas */}
      <rect width="300" height="450" fill={`url(#bg_grad_${seed})`} />

      {/* Genre Visual Composition */}
      {renderComposition()}

      {/* Film Title Zone (Auto-fitting typography) */}
      <g transform="translate(24, 76)">
        <text
          x="0"
          y="0"
          fill="#f2efe6"
          fontSize={titleFontSize}
          fontWeight="700"
          fontFamily="system-ui, -apple-system, sans-serif"
          letterSpacing="0.04em"
          style={{ textTransform: "uppercase" }}
        >
          {title.length > 28 ? (
            <>
              <tspan x="0" dy="0">{title.slice(0, 24)}...</tspan>
            </>
          ) : (
            title
          )}
        </text>

        {/* Year and Genre Tagline */}
        <text
          x="0"
          y="26"
          fill={pal.accent}
          fontSize="11"
          fontWeight="600"
          fontFamily="monospace"
          letterSpacing="0.14em"
          opacity="0.85"
        >
          {year ? `${year} • ` : ""}{primaryGenre.toUpperCase()}
        </text>
      </g>

      {/* Subtle Bottom Billing Block (Film craft detail) */}
      <g transform="translate(24, 412)" opacity="0.35">
        <line x1="0" y1="0" x2="252" y2="0" stroke="#f2efe6" strokeWidth="0.5" opacity="0.3" />
        <text x="0" y="14" fill="#f2efe6" fontSize="7" fontFamily="monospace" letterSpacing="0.15em">
          CINEMATIQUE ORIGINAL • SOUNDTRACK & VISUALS
        </text>
      </g>

      {/* Fine Film Grain Layer */}
      <rect width="300" height="450" filter={`url(#grain_${seed})`} opacity="0.6" pointerEvents="none" />
    </svg>
  );
};
