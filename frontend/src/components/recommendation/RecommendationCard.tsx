import { Leaf, Sprout, CalendarDays, Clock, AlertTriangle, FlaskConical } from "lucide-react";
import type { CropRecommendation, FertilizerRecommendation } from "../../types/recommendation";
import { useT } from "../../i18n/useT";

/* ─── helpers ──────────────────────────────────────────────────────────── */

/** Split a long reason string into the leading sentences and a trailing note.
 *  The first 2 sentences become the "why" block; the rest become the "note" block.
 *  This avoids one giant paragraph without inventing data.
 */
function splitReason(reason: string): { why: string; note: string } {
  const sentences = reason
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
  if (sentences.length <= 2) return { why: reason.trim(), note: "" };
  const why = sentences.slice(0, 2).join(" ");
  const note = sentences.slice(2).join(" ");
  return { why, note };
}

/* ─── Crop Card ─────────────────────────────────────────────────────────── */

function CropCard({ item }: { item: CropRecommendation }) {
  const t = useT();
  const { why, note } = splitReason(item.reason);

  return (
    <article className="rec-item rec-item--crop">
      {/* Name row */}
      <div className="rec-item-header">
        <div className="rec-item-icon rec-item-icon--crop">
          <Sprout size={18} />
        </div>
        <div className="rec-item-title-group">
          <h3 className="rec-item-name">{item.crop}</h3>
          <div className="rec-item-badges">
            {item.season && (
              <span className="rec-tag">
                <CalendarDays size={11} />
                {item.season}
              </span>
            )}
            {item.expected_duration_days && (
              <span className="rec-tag">
                <Clock size={11} />
                {item.expected_duration_days} days
              </span>
            )}
            <span className="rec-suitability">
              {item.suitability}% {t("suitabilityScore")}
            </span>
          </div>
        </div>
      </div>

      {/* Why recommended */}
      <div className="rec-item-body">
        <p className="rec-item-why">{why}</p>

        {/* Extra guidance note */}
        {note && (
          <p className="rec-item-note">{note}</p>
        )}
      </div>
    </article>
  );
}

/* ─── Fertilizer Card ───────────────────────────────────────────────────── */

function FertilizerCard({ item }: { item: FertilizerRecommendation }) {
  const { why, note } = splitReason(item.reason);

  return (
    <article className="rec-item rec-item--fert">
      {/* Name row */}
      <div className="rec-item-header">
        <div className="rec-item-icon rec-item-icon--fert">
          <FlaskConical size={18} />
        </div>
        <div className="rec-item-title-group">
          <h3 className="rec-item-name">{item.name}</h3>
          <div className="rec-item-badges">
            {item.type && (
              <span className={`rec-type-badge rec-type-badge--${item.type}`}>
                {item.type === "organic" ? "Organic" : item.type === "inorganic" ? "Inorganic" : item.type}
              </span>
            )}
            {item.quantity && (
              <span className="rec-tag">
                <Leaf size={11} />
                {item.quantity}
              </span>
            )}
            {item.frequency && (
              <span className="rec-tag">
                <Clock size={11} />
                {item.frequency}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Why recommended */}
      <div className="rec-item-body">
        <p className="rec-item-why">{why}</p>

        {/* Guidance / continuation */}
        {note && (
          <p className="rec-item-note">{note}</p>
        )}

        {/* Precautions */}
        {item.precautions && item.precautions.length > 0 && (
          <div className="rec-item-precautions">
            <span className="rec-precautions-label">
              <AlertTriangle size={12} />
              Important
            </span>
            <ul className="rec-precautions-list">
              {item.precautions.map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </article>
  );
}

/* ─── Public export ─────────────────────────────────────────────────────── */

export default function RecommendationCard({
  item,
}: {
  item: CropRecommendation | FertilizerRecommendation;
}) {
  if ("crop" in item) return <CropCard item={item} />;
  return <FertilizerCard item={item as FertilizerRecommendation} />;
}
