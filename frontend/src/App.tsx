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
  }, []);

  const chartData = useMemo(() => {
    if (!run) return [];
    const first = Object.values(run.series)[0] ?? [];
    return first.map((p) => ({
      week: p.week_index + 1,
      profit: Number(p.gross_profit.toFixed(2)),
      quantity: Number(p.quantity.toFixed(2)),
    }));
  }, [run]);

  async function seedAndSimulate() {
    setBusy(true);
    setStatus("");
    try {
      let list = products;
      if (list.length === 0) {
