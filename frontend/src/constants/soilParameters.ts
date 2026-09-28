export const SOIL_PARAMETERS = [
  { key: "ph", label: "pH", unit: "", min: 0, max: 14 },
  { key: "nitrogen", label: "Nitrogen", unit: "kg/ha", min: 0, max: 300 },
  { key: "phosphorus", label: "Phosphorus", unit: "kg/ha", min: 0, max: 150 },
  { key: "potassium", label: "Potassium", unit: "kg/ha", min: 0, max: 500 },
  { key: "ec", label: "EC", unit: "dS/m", min: 0, max: 20 },
  { key: "moisture", label: "Moisture", unit: "%", min: 0, max: 100 },
  { key: "temperature", label: "Temperature", unit: "°C", min: -20, max: 80 },
  { key: "organic_carbon", label: "Organic Carbon", unit: "%", min: 0, max: 10 }
] as const;
