import { redirect } from "next/navigation";

/** Redirect legacy "New campaign" route to the unified create flow (Recommendations). */
export default function NewCampaignPage() {
  redirect("/dashboard/recommendations");
}
