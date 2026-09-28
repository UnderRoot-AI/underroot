import { Leaf, Sprout, Clock, CalendarDays, CheckCircle2, AlertTriangle } from "lucide-react";
import type { CropRecommendation, FertilizerRecommendation } from "../../types/recommendation";
import { useT } from "../../i18n/useT";

export default function RecommendationCard({ item }: { item: CropRecommendation | FertilizerRecommendation }) {
  const isCrop = "crop" in item;
  const t = useT();

  return (
    <article className="recommendation-card">
      {/* Header row */}
      <div className="recommendation-title">
        <div className="recommendation-icon">{isCrop ? <Sprout /> : <Leaf />}</div>
        <div>
          <h3>{isCrop ? item.crop : item.name}</h3>
          {isCrop && (
            <span className="rec-badge">
              {item.suitability}% {t("suitabilityScore")}
            </span>
          )}
          {!isCrop && (item as FertilizerRecommendation).type && (
            <span className="rec-badge rec-badge--type">
              {(item as FertilizerRecommendation).type}
            </span>
          )}
        </div>
      </div>

      {/* Meta row */}
      <div className="rec-meta">
        {"season" in item && item.season && (
          <span><CalendarDays size={13} /> {t("season")}: <strong>{item.season}</strong></span>
        )}
        {"expected_duration_days" in item && item.expected_duration_days && (
          <span><Clock size={13} /> {t("growthPeriod")}: <strong>{item.expected_duration_days} days</strong></span>
        )}
        {"quantity" in item && item.quantity && (
          <span><Leaf size={13} /> {t("applicationRate")}: <strong>{item.quantity}</strong></span>
        )}
        {"frequency" in item && item.frequency && (
          <span><Clock size={13} /> {t("frequency")}: <strong>{item.frequency}</strong></span>
        )}
      </div>

      {/* Main advice */}
      <p className="rec-reason">{item.reason}</p>

      {/* Precautions */}
      {"precautions" in item && item.precautions && item.precautions.length > 0 && (
        <ul className="rec-precautions">
          {item.precautions.map((p, i) => (
            <li key={i}>
              <AlertTriangle size={12} />
              {p}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
