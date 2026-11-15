import * as Notifications from "expo-notifications";
export type LocalNotice = { id: string; at: Date; title: string; body: string };

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

// Re-planning keeps one notification per item and drops the ones no longer
// wanted; each caller owns its own identifier prefix.
export async function scheduleLocal(prefix: string, items: LocalNotice[]) {
  let { granted } = await Notifications.getPermissionsAsync();
  if (!granted) ({ granted } = await Notifications.requestPermissionsAsync());
  if (!granted) return;
  const scheduled = await Notifications.getAllScheduledNotificationsAsync();
  const wanted = new Set(items.map((i) => prefix + i.id));
  for (const n of scheduled)
    if (n.identifier.startsWith(prefix) && !wanted.has(n.identifier))
      await Notifications.cancelScheduledNotificationAsync(n.identifier);
  const have = new Set(scheduled.map((n) => n.identifier));
  for (const item of items)
    if (!have.has(prefix + item.id))
      await Notifications.scheduleNotificationAsync({
        identifier: prefix + item.id,
        content: { title: item.title, body: item.body },
        trigger: {
          type: Notifications.SchedulableTriggerInputTypes.DATE,
          date: item.at,
        },
      });
}
