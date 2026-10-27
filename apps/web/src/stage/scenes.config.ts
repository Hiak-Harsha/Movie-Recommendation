export interface SceneConfig {
  id: string;
  moduleId: "hero" | "search" | "taste" | "foryou" | "tune" | "library" | "closing";
  number: string;
  label: string;
  startVh: number;
  endVh: number;
  hash: string;
}

export const TOTAL_STORY_VH = 700;

export const SCENES: SceneConfig[] = [
  {
    id: "scene00",
    moduleId: "hero",
    number: "00",
    label: "Cinema Showcase",
    startVh: 0,
    endVh: 100,
    hash: "#showcase",
  },
  {
    id: "scene01",
    moduleId: "search",
    number: "01",
    label: "Search Films",
    startVh: 100,
    endVh: 180,
    hash: "#search",
  },
  {
    id: "scene02",
    moduleId: "taste",
    number: "02",
    label: "Pick Your Favourites",
    startVh: 180,
    endVh: 300,
    hash: "#taste",
  },
  {
    id: "scene03",
    moduleId: "foryou",
    number: "03",
    label: "Curated For You",
    startVh: 300,
    endVh: 440,
    hash: "#for-you",
  },
  {
    id: "scene04",
    moduleId: "tune",
    number: "04",
    label: "Tune Your Experience",
    startVh: 440,
    endVh: 540,
    hash: "#tune",
  },
  {
    id: "scene05",
    moduleId: "library",
    number: "05",
    label: "Tonight's Lineup",
    startVh: 540,
    endVh: 620,
    hash: "#library",
  },
  {
    id: "scene06",
    moduleId: "closing",
    number: "06",
    label: "Credits & About",
    startVh: 620,
    endVh: 700,
    hash: "#closing",
  },
];
