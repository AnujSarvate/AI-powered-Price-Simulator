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
        const created = await api.createProduct({
          sku: "MUG-001",
          name: "Coffee Mug",
          unit_cost: 4,
          list_price: 12,
          category: "merch",
          elasticity: 1.2,
          q0: 80,
        });
        list = [created];
        setProducts(list);
      }
      const scenario = await api.createScenario({
        name: "Dashboard demo",
        horizon_weeks: 12,
        product_ids: list.map((p) => p.product_id),
      });
      const simulation = await api.simulate(scenario.scenario_id);
      setRun(simulation);
      setStatus(`Simulation complete. Total profit: $${simulation.total_profit.toFixed(2)}`);
    } catch (e) {
      setStatus(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function trainModel() {
    setBusy(true);
    try {
      const res = await api.trainModel();
      setStatus(`Model ${res.model_id.slice(0, 8)}… MAE=${res.metrics.mae?.toFixed(2)}`);
    } catch (e) {
      setStatus(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>AI-Powered Price Simulator</h1>
      <p>Elasticity simulation, optimization API, and demand ML training.</p>

      <div className="card row">
        <button disabled={busy} onClick={seedAndSimulate}>
          Run 12-week simulation
        </button>
        <button disabled={busy} onClick={trainModel}>
          Train demand model
        </button>
        <span>{status}</span>
      </div>

      <div className="card">
        <h2>Products ({products.length})</h2>
        <ul>
          {products.map((p) => (
            <li key={p.product_id}>
              {p.name} — ${p.list_price.toFixed(2)} (ε={p.elasticity})
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
