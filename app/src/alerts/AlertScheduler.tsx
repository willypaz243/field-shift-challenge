import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useOffline } from "../offline/provider";
import { alertRows } from "./alerts";
import { scheduleAlerts } from "./notify";
import { notificationPlan } from "./plan";
import { notificationText } from "./text";

export function AlertScheduler() {
  const { t } = useTranslation();
  const { data } = useOffline();
  useEffect(() => {
    if (!data) return;
    const plan = notificationPlan(alertRows(data.alertas, new Set()));
    void scheduleAlerts(plan, (p) => notificationText(p.alert, t)).catch(
      () => undefined,
    );
  }, [data, t]);
  return null;
}
