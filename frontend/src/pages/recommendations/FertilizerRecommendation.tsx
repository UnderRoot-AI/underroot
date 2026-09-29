import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Loading from "../../components/common/Loading";
import EmptyState from "../../components/common/EmptyState";
import RecommendationCard from "../../components/recommendation/RecommendationCard";
import { recommendationApi } from "../../services/recommendation.api";
import type { FertilizerRecommendation } from "../../types/recommendation";
import { Leaf } from "lucide-react";
import { useT } from "../../i18n/useT";

export default function FertilizerRecommendationPage() {
  const [params] = useSearchParams();
  const testId = params.get("test");
  const t = useT();
  const [items, setItems] = useState<FertilizerRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    recommendationApi
      .fertilizer(testId || undefined)
      .then(setItems)
      .catch((e) => setError(e.response?.data?.detail || t("noFertRecs")))
      .finally(() => setLoading(false));
  }, [testId]);

  return (
    <>
      <PageHeader title={t("fertRecTitle")} subtitle={t("fertRecSubtitle")} />
      <Card>
        {loading ? (
          <Loading />
        ) : error ? (
          <div className="alert alert-error">{error}</div>
        ) : items.length ? (
          <section className="rec-section">
            <h2 className="rec-section-heading">{t("recommendedFertilizers")}</h2>
            <div className="rec-list">
              {items.map((x, i) => (
                <RecommendationCard key={i} item={x} />
              ))}
            </div>
          </section>
        ) : (
          <EmptyState
            icon={<Leaf />}
            title={t("noFertRecs")}
            text={t("runTestFirst")}
          />
        )}
      </Card>
    </>
  );
}
