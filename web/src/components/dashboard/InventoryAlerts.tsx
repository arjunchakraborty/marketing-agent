import type { InventoryAlert } from "@/types/analytics";

interface InventoryAlertsProps {
  alerts: InventoryAlert[];
}

const priorityStyles: Record<InventoryAlert["priority"], string> = {
  high: "bg-rose-100 text-rose-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-emerald-100 text-emerald-700",
};

export function InventoryAlerts({ alerts }: InventoryAlertsProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-700">Inventory Alerts</h3>
      </div>
      <ul className="divide-y divide-slate-200">
        {alerts.map((alert) => (
          <li key={alert.sku} className="flex flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-800">{alert.productName}</p>
              <p className="text-xs uppercase tracking-wide text-slate-500">SKU: {alert.sku}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${priorityStyles[alert.priority]}`}>
                {alert.priority.toUpperCase()}
              </span>
              <p className="text-xs font-medium text-slate-500">{alert.daysRemaining} days remaining</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
