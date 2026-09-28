import { useEffect, useState } from "react";
import { ExternalLink, Landmark } from "lucide-react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/ui/Card";
import Loading from "../../components/common/Loading";
import { resourcesApi, type ResourceItem } from "../../services/resources.api";
import { useT } from "../../i18n/useT";

export default function GovernmentResources() {
  const [items, setItems] = useState<ResourceItem[]>([]);
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(true);
  const t = useT();

  useEffect(() => {
    resourcesApi.government()
      .then(x => { setItems(x.items); setNote(x.note); })
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <PageHeader title={t("resourcesTitle")} subtitle={t("resourcesSubtitle")} />
      <Card>
        {loading ? <Loading /> : (
          <div className="resource-list">
            {items.length === 0 ? (
              <p className="muted">{t("noResourcesFound")}</p>
            ) : (
              items.map(x => (
                <a className="resource-card" href={x.url} target="_blank" rel="noreferrer" key={x.url}>
                  <div className="recommendation-icon"><Landmark size={18} /></div>
                  <div>
                    <div className="recommendation-title">
                      <h3>{x.name}</h3>
                      <ExternalLink size={14} />
                    </div>
                    <p>{x.description}</p>
                    <small>{x.url}</small>
                  </div>
                </a>
              ))
            )}
            <p className="muted">{note}</p>
          </div>
        )}
      </Card>
    </>
  );
}
