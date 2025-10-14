export function scoreColor(score: number) {
    if (score >= 75) return "bg-green-600";
    if (score >= 55) return "bg-yellow-500";
    return "bg-red-600";
  }
  