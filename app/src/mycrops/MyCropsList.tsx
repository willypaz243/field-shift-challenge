import { useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";
import { Colors, Radius, Typography } from "../../constants/Theme";
import type { MyCrop } from "../farm/my-crops";
import { useOffline } from "../offline/provider";
import { cropImages } from "../ui/crop-images";
import { laPazToday } from "../ui/dates";
import { Sheet } from "../ui/Sheet";
import { Harvests, dueHarvest } from "./mycrops";
import { MyCropSheet, ResultButtons, useAnswerHarvest } from "./MyCropSheet";
import { cropName, notifyMyCrops, useMyCrops } from "./use-my-crops";

// "Todavía no" asks again a few days later instead of every time Hoy opens.
const ASK_AGAIN_DAYS = 3;
const DAY_MS = 86_400_000;

function progress(crop: MyCrop, today: string) {
  const start = Date.parse(crop.siembra);
  const total = Date.parse(crop.cosecha) - start;
  return Math.min(
    100,
    Math.max(4, ((Date.parse(today) - start) / total) * 100),
  );
}

export function MyCropsList({ emptyText }: { emptyText: string }) {
  const { t } = useTranslation();
  const { client, data } = useOffline();
  const { crops, states } = useMyCrops();
  const answer = useAnswerHarvest();
  const [open, setOpen] = useState<MyCrop | null>(null);
  const today = laPazToday();
  const active = crops.filter((c) => !states.get(c.id)?.resultado);
  const due = dueHarvest(crops, states, today);

  const later = async (crop: MyCrop) => {
    const until = new Date(Date.parse(today) + ASK_AGAIN_DAYS * DAY_MS)
      .toISOString()
      .slice(0, 10);
    await new Harvests(client.store.db).postpone(crop.id, until);
    notifyMyCrops();
  };

  return (
    <>
      {active.length === 0 ? (
        <Text style={styles.empty}>{emptyText}</Text>
      ) : (
        <View style={styles.list}>
          {active.map((crop, i) => (
            <Pressable
              key={crop.id}
              accessibilityRole="button"
              onPress={() => setOpen(crop)}
              style={({ pressed }) => [
                styles.row,
                i > 0 && styles.divider,
                pressed && styles.pressed,
              ]}
            >
              <Text style={styles.name}>{cropName(data, crop.crop_id)}</Text>
              <View style={styles.bar}>
                <View
                  style={[styles.fill, { width: `${progress(crop, today)}%` }]}
                />
              </View>
              <Ionicons name="chevron-forward" size={22} color={Colors.field} />
            </Pressable>
          ))}
        </View>
      )}
      <MyCropSheet crop={open} onClose={() => setOpen(null)} />
      {due && (
        <Sheet
          visible
          dismissable={false}
          title={t("cultivos.pregunta", {
            cultivo_min: cropName(data, due.crop_id).toLowerCase(),
          })}
          closeLabel={t("comun.cerrar")}
          onClose={() => undefined}
        >
          {cropImages[due.crop_id] && (
            <Image
              source={cropImages[due.crop_id]}
              style={styles.hero}
              resizeMode="cover"
            />
          )}
          <ResultButtons onPick={(r) => void answer(due, r)} />
          <Pressable
            accessibilityRole="button"
            onPress={() => void later(due)}
            style={styles.later}
          >
            <Text style={styles.laterText}>{t("cultivos.todavia_no")}</Text>
          </Pressable>
        </Sheet>
      )}
    </>
  );
}

const styles = StyleSheet.create({
  empty: { ...Typography.body, color: Colors.ink2 },
  list: {
    borderWidth: 1,
    borderColor: Colors.line,
    borderRadius: Radius.card,
    overflow: "hidden",
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    minHeight: 64,
    paddingHorizontal: 14,
  },
  divider: { borderTopWidth: 1, borderTopColor: Colors.line },
  pressed: { backgroundColor: Colors.paper2 },
  name: { ...Typography.label, fontSize: 19, color: Colors.ink, width: 110 },
  bar: {
    flex: 1,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.paper2,
    overflow: "hidden",
  },
  fill: { height: "100%", backgroundColor: Colors.field },
  hero: { width: "100%", height: 260, borderRadius: Radius.card },
  later: { minHeight: 56, alignItems: "center", justifyContent: "center" },
  laterText: {
    ...Typography.label,
    fontSize: 19,
    color: Colors.ink2,
    textDecorationLine: "underline",
  },
});
