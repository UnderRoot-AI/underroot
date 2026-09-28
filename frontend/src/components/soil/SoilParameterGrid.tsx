import type { SoilParameters } from "../../types/soil";
import ParameterCard from "./ParameterCard";

export default function SoilParameterGrid({ parameters }: { parameters: SoilParameters }) {
  const items = [
    ["pH", parameters.ph, ""],
    ["Nitrogen", parameters.nitrogen, "kg/ha"],
    ["Phosphorus", parameters.phosphorus, "kg/ha"],
    ["Potassium", parameters.potassium, "kg/ha"],
    ["EC", parameters.ec, "dS/m"],
    ["Moisture", parameters.moisture, "%"],
    ["Temperature", parameters.temperature, "°C"],
    ["Organic Carbon", parameters.organic_carbon, "%"]
  ] as const;
  return <div className="parameter-grid">{items.map(([label, value, unit]) => <ParameterCard key={label} label={label} value={value} unit={unit} />)}</div>;
}
