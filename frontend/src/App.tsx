import AppRoutes from "./routes/AppRoutes";
import { useGlobalTranslation } from "./i18n/useGlobalTranslation";

export default function App() {
  useGlobalTranslation();
  return <AppRoutes />;
}
