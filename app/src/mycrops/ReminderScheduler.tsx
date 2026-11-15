import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { scheduleLocal } from "../alerts/notify";
import { useOffline } from "../offline/provider";
import { shortDate } from "../ui/dates";
import { reminderPlan } from "./mycrops";
import { cropName, useMyCrops } from "./use-my-crops";

// Reminders have no time in the list; the phone still rings at 6:00 La Paz (10:00 UTC).
const SIX_AM_UTC = 10;

export function ReminderScheduler() {
  const { t } = useTranslation();
  const { data } = useOffline();
  const { crops, states } = useMyCrops();
  useEffect(() => {
    const now = new Date();
    const items = reminderPlan(
      crops.filter((c) => !states.get(c.id)?.resultado),
    )
      .map((r) => {
        const at = new Date(`${r.fecha}T00:00:00Z`);
        at.setUTCHours(SIX_AM_UTC);
        const cultivo = cropName(data, r.crop.crop_id);
        return {
          id: r.id,
          at,
          title: t(`cultivos.recordatorio.${r.tipo}`, {
            cultivo,
            cultivo_min: cultivo.toLowerCase(),
          }),
          body: t(`cultivos.recordatorio_detalle.${r.tipo}`, {
            fecha: shortDate(r.crop.cosecha),
          }),
        };
      })
      .filter((i) => i.at > now);
    void scheduleLocal("recordatorio:", items).catch(() => undefined);
  }, [crops, states, data, t]);
  return null;
}
