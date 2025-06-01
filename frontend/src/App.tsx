import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, Product, SimulationRun } from "./api";

export default function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [run, setRun] = useState<SimulationRun | null>(null);
  const [status, setStatus] = useState<string>("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .listProducts()
      .then(setProducts)
      .catch((e) => setStatus(String(e)));
