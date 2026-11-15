import * as Notifications from "expo-notifications";
import type { Planned } from "./plan";

const PREFIX = "alerta:";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

// Re-planning on every sync keeps one notification per alert and notice day,
// and drops the ones whose alert is gone.
export async function scheduleAlerts(
  plan: Planned[],
  text: (p: Planned) => { title: string; body: string },
) {
  let { granted } = await Notifications.getPermissionsAsync();
  if (!granted) ({ granted } = await Notifications.requestPermissionsAsync());
  if (!granted) return;
  const scheduled = await Notifications.getAllScheduledNotificationsAsync();
  const wanted = new Set(plan.map((p) => PREFIX + p.id));
  for (const n of scheduled)
    if (n.identifier.startsWith(PREFIX) && !wanted.has(n.identifier))
      await Notifications.cancelScheduledNotificationAsync(n.identifier);
  const have = new Set(scheduled.map((n) => n.identifier));
  for (const p of plan)
    if (!have.has(PREFIX + p.id))
      await Notifications.scheduleNotificationAsync({
        identifier: PREFIX + p.id,
        content: text(p),
        trigger: {
          type: Notifications.SchedulableTriggerInputTypes.DATE,
          date: p.at,
        },
      });
}
