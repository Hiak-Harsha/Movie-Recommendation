/**
 * CineMatch - About Module Copy
 * Contains technical documentation, dataset citations, evaluation details, and legal notices.
 */

export const aboutCopy = {
  title: "About CineMatch",
  subtitle: "Architecture, data provenance, and recommendation methodology",
  tabs: {
    howToUse: "How to use",
    howItWorks: "How it works",
    dataCredits: "Data & Credits",
    terms: "Terms & Privacy",
    modelReport: "Model Report",
  },
  howToUse: {
    steps: [
      {
        number: "01",
        title: "Search or Explore",
        desc: "Use the search bar or scroll through the curated showcase to discover films across genres and decades.",
      },
      {
        number: "02",
        title: "Pick 5 Films You Love",
        desc: "Rate or bookmark 5 films to build your taste profile. CineMatch dynamically folds your preferences into the vector space.",
      },
      {
        number: "03",
        title: "Explore Your Curated Shelves",
        desc: "Review your personalized shelves, including reasonings for why each film was recommended.",
      },
      {
        number: "04",
        title: "Fine-tune and Save",
        desc: "Adjust the discovery, variety, and era sliders in real-time, then save your favorites to your cinema lineup.",
      },
    ],
    shortcuts: [
      { key: "⌘K or /", action: "Open film search" },
      { key: "?", action: "Open About & Model Report" },
      { key: "Esc", action: "Close drawer or detail modal" },
      { key: "Space / Enter", action: "Select or rate movie" },
    ],
    tips: "Tip: Rate more films across diverse genres to increase recommendation precision. Use the Tune sliders to control whether you want familiar classics or obscure gems.",
  },
  howItWorks: {
    summary:
      "We look at films people with similar taste rated highly, films that resemble ones you loved, and popular titles across your favorite genres and eras. We combine these signals into a balanced list tailored to your taste profile.",
    technicalTitle: "Technical Architecture & Pipeline",
    technicalDetails: [
      {
        component: "Candidate Generation",
        detail:
          "Combines Alternating Least Squares (ALS) latent factors, Item-Item k-Nearest Neighbors on cosine similarity, and TF-IDF content vectors computed from genres and user tags.",
      },
      {
        component: "Cold-Start Handling",
        detail:
          "Zero-ratings: Bayesian smoothed popularity. 1-4 ratings: Fast closed-form ALS fold-in combined with content similarity. 5+ ratings: Full hybrid ranker.",
      },
      {
        component: "Re-Ranking & Diversity",
        detail:
          "Maximal Marginal Relevance (MMR) balances relevance and diversity, while user faders adjust novelty, decade recency, and genre weights.",
      },
    ],
  },
  dataCredits: {
    movieLensCitation:
      "F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context. ACM Transactions on Interactive Intelligent Systems (TiiS) 5, 4, Article 19 (December 2015).",
    licenseNotice:
      "The MovieLens dataset is provided by GroupLens Research at the University of Minnesota for educational and research purposes. Non-commercial use only.",
    tmdbAttribution:
      "This product uses the TMDB API but is not endorsed or certified by TMDB. Movie posters and metadata are sourced from The Movie Database (TMDB).",
  },
  terms: {
    purpose:
      "CineMatch is an educational, non-commercial movie recommendation system designed to demonstrate modern hybrid recommender systems and cinematic web interfaces.",
    cookieNotice:
      "We use a single signed functional cookie (cm_sid) to persist your personal taste profile, ratings, and watchlist across sessions. No third-party tracking or advertising cookies are used.",
    exportHeading: "Data Portability & Erasure",
    exportDesc: "You have full ownership of your data. You can download or permanently erase your profile at any time.",
    exportButton: "Export My Data (JSON)",
    eraseButton: "Erase My Data",
    eraseConfirm: "Are you sure? This will delete all your ratings, saved films, and session history.",
  },
  modelReport: {
    heading: "Offline Evaluation & Benchmark Report",
    protocolTitle: "Evaluation Protocol",
    protocolDesc:
      "Evaluated on a strictly temporal, user-isolated split with zero data leakage. Metrics reported across held-out positive test ratings (ratings >= 4.0).",
    tableHeaders: {
      strategy: "Strategy",
      ndcg10: "NDCG@10",
      map10: "MAP@10",
      precision10: "Precision@10",
      recall10: "Recall@10",
    },
    coldStartNote:
      "Cold-start curves show performance progression from Tier 0 (unrated) through Tier 2 (fully calibrated profile).",
    liveStrategyBadge: "Active Serving Strategy: {strategy}",
  },
};
