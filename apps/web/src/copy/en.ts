/**
 * CineMatch - Visitor-First Surface Copy
 * Strictly adheres to visitor-first rules: focus on films and next watch.
 */

export const surfaceCopy = {
  brand: {
    name: "CINEMATCH",
    tagline: "Find your next favourite film.",
    subtitle: "Pick a few movies you love. We'll do the rest.",
  },
  nav: {
    startPicking: "Start picking",
    searchFilms: "Search films",
    about: "About",
    aboutCredits: "About and credits",
    myPicks: "My picks",
    library: "Library",
    continue: "Continue",
    skipIntro: "Skip intro",
    reduceMotion: "Reduce motion",
  },
  dock: {
    searchHint: "Search",
    searchShortcut: "⌘K",
    picksCount: "Picks",
    libraryCount: "Library",
    info: "About CineMatch",
    steps: {
      0: "Welcome",
      1: "Search",
      2: "Taste",
      3: "For You",
      4: "Tune",
      5: "Library",
      6: "Credits",
    },
  },
  scenes: {
    s00: {
      eyebrow: "00 / Welcome",
      heading: "Cinema tailored to your exact taste.",
      scrollPrompt: "Scroll to explore",
    },
    s01: {
      eyebrow: "01 / Search",
      heading: "Search the film universe.",
      placeholderPrefix: "Search titles, e.g. ",
      placeholders: [
        "Inception",
        "Pulp Fiction",
        "Spirited Away",
        "The Dark Knight",
        "Parasite",
        "Casablanca",
        "Blade Runner",
      ],
      noResults: "No movies found matching that title. Try another search or explore trending titles.",
    },
    s02: {
      eyebrow: "02 / Taste",
      heading: "Tell us what you love.",
      subheading: "Tap movies you've enjoyed to calibrate your personal recommendations.",
      counter: "{count} of 5 selected",
      counterReady: "Your picks are ready",
      skip: "Haven't seen it",
      popularAlternative: "Show me popular films instead",
    },
    s03: {
      eyebrow: "03 / For You",
      heading: "Your curated shelves.",
      subheading: "Discovered just for you, refreshed as your taste evolves.",
      turnOverCard: "Why this was picked",
      notInterested: "Not interested",
      shelfTitles: {
        topPicks: "Top picks for you",
        becauseYouLiked: "Because you liked {title}",
        hiddenGems: "Hidden gems in {genre}",
        fromDecade: "From a decade you love",
        popularNow: "Popular right now",
      },
    },
    s04: {
      eyebrow: "04 / Tune",
      heading: "Fine-tune your recommendations.",
      subheading: "Dial in novelty, diversity, and release eras in real-time.",
      sliders: {
        novelty: {
          label: "Discovery style",
          left: "Familiar classics",
          right: "Hidden gems",
        },
        diversity: {
          label: "Genre variety",
          left: "Focused match",
          right: "Eclectic mix",
        },
        recency: {
          label: "Release era",
          left: "Timeless",
          right: "Recent releases",
        },
      },
      chips: {
        allGenres: "All genres",
        allDecades: "All decades",
        reset: "Reset filters",
      },
    },
    s05: {
      eyebrow: "05 / Library",
      heading: "Tonight's lineup.",
      subheading: "Films you've saved for later, formatted as cinema ticket stubs.",
      emptyHeading: "Your library is waiting.",
      emptyAction: "Browse films and tap the bookmark icon to start your lineup.",
      markWatched: "Mark as watched",
      remove: "Remove",
      tearTicket: "Tear ticket",
    },
    s06: {
      eyebrow: "06 / Closing",
      heading: "Great stories are waiting to be watched.",
      subheading: "Scroll back anytime, or open About to see how CineMatch was built.",
      backToTop: "Back to top",
    },
  },
  card: {
    badges: {
      topPick: "Top pick",
      hiddenGem: "Hidden gem",
      fanFavorite: "Fan favourite",
      popular: "Popular",
    },
    save: "Save to lineup",
    saved: "Saved",
    rate: "Rate",
    viewDetails: "View details",
    reasons: {
      highRating: "Highly rated by cinema fans with similar taste",
      similarToLoved: "Shares themes and tone with films you loved",
      timelessClassic: "A celebrated landmark from this era",
    },
  },
  common: {
    undo: "Undo",
    close: "Close",
    loading: "Loading films...",
    error: "Something went wrong loading this section. Please try again.",
    retry: "Try again",
  },
  footer: {
    logo: "CINEMATCH",
    about: "About",
    terms: "Terms & Privacy",
    credits: "Data & Credits",
    tmdbNotice: "Movie data and poster artwork provided by TMDB.",
  },
};
