import { InventoryAlerts } from "@/components/dashboard/InventoryAlerts";
import { inventoryAlerts } from "@/lib/seedData";

export default function InventoryPage() {
  return (
    <div className="p-6 md:p-10">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">Inventory</h1>
        <p className="mt-1.5 text-zinc-600 dark:text-zinc-400">
          Inventory alerts and low-stock items.
        </p>
      </div>
      <section>
        <InventoryAlerts alerts={inventoryAlerts} />
      </section>
    </div>
  );
}
