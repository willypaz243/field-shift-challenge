import type { Alert } from "./alerts";

export type Planned = {
  id: string;
  alert: Alert;
  daysBefore: number;
  at: Date;
};

// API-CONTRACT §6: 6:00 in La Paz (UTC-4, no daylight saving), 7 days before
// when the alert is not low-confidence, and 1 day before.
const SIX_AM_UTC = 10;
const NOTICES = [7, 1];

export function notificationPlan(
  alertas: Alert[],
  now = new Date(),
): Planned[] {
  const plan: Planned[] = [];
  for (const alert of alertas) {
    if (!alert.fecha_evento) continue;
    for (const daysBefore of NOTICES) {
      if (daysBefore === 7 && alert.confianza === "baja") continue;
      const at = new Date(`${alert.fecha_evento}T00:00:00Z`);
      at.setUTCDate(at.getUTCDate() - daysBefore);
      at.setUTCHours(SIX_AM_UTC);
      if (at > now)
        plan.push({ id: `${alert.id}:${daysBefore}`, alert, daysBefore, at });
    }
  }
  return plan.sort((a, b) => a.at.getTime() - b.at.getTime());
}
