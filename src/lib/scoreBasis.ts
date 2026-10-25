import type { Programme } from "../types/jupas";

// Programmes whose SCORING runs on the 2027 weighting because their 2026
// benchmarks are already on that basis: the institution republished
// recalculated scores (CityU across the board, CUHK JS4725), or the benchmark
// was rebuilt onto the new weighting (HKBU introduced-weighting programmes,
// CUHK grade-profile simulations, HKUST Engineering's official simulated
// scores). Everything else scores on true 2026 logic per the Year-Labeling
// Rule. UI year labels ("Calculated based on {year} formula", "Method
// ({year})") read this so they state the basis actually used.
const BASES_2027 = new Set([
  "cityu_2027_recalculated",
  "cuhk_2027_recalculated",
  "cuhk_2027_simulated",
  "eduhk_2027_recalculated",
  "hkbu_2027_simulated",
]);

export function scoringBasisYear(_programme: Programme): "2026" | "2027" {
  // 2027 cycle: every score is calculated with the 2027 weighting. The
  // 2026 benchmarks are shown for reference and carry their own basis note.
  return "2027";
}
