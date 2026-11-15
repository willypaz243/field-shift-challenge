import { useEffect } from "react";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTranslation } from "react-i18next";
import { Colors, Radius, Spacing, Typography } from "../constants/Theme";
import { alertRows } from "../src/alerts/alerts";
import { alertDetail, alertTitle, alertWhen } from "../src/alerts/text";
import { useSeenAlerts } from "../src/alerts/use-seen";
import { useOffline } from "../src/offline/provider";

type Icon = keyof typeof Ionicons.glyphMap;
const LOOK: Record<string, { icon: Icon; color: string; bg: string }> = {
  helada: { icon: "snow-outline", color: Colors.frost, bg: Colors.frostSoft },
  granizo: { icon: "thunderstorm-outline", color: Colors.ink, bg: Colors.paper2 },
  lluvia_fuerte: { icon: "rainy-outline", color: Colors.water, bg: Colors.waterSoft },
  desborde: { icon: "water", color: Colors.water, bg: Colors.waterSoft },
  sequia: { icon: "sunny-outline", color: Colors.dry, bg: Colors.drySoft },
  represa_baja: { icon: "water-outline", color: Colors.dry, bg: Colors.drySoft },
  temporada: { icon: "calendar-outline", color: Colors.water, bg: Colors.waterSoft },
};

export default function AvisosScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { data } = useOffline();
  const { seen, markSeen } = useSeenAlerts();
  // Freeze "Nuevo" for this visit, then mark everything shown as seen.
  const rows = alertRows(data?.alertas, seen);
  useEffect(() => {
    const ids = alertRows(data?.alertas, new Set()).map((a) => a.id);
    if (ids.length) {
      const timer = setTimeout(() => void markSeen(ids), 1500);
      return () => clearTimeout(timer);
    }
  }, [data, markSeen]);

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.status}>
        <Pressable accessibilityRole="button" onPress={() => router.back()} style={styles.back}>
          <Ionicons name="chevron-back" size={24} color={Colors.ink} />
          <Text style={styles.backText}>{t("comun.atras")}</Text>
        </Pressable>
      </View>
      <ScrollView contentContainerStyle={styles.wall}>
        <Text style={styles.title}>{t("avisos.titulo")}</Text>
        <Text style={styles.section}>{t("avisos.alertas")}</Text>
        <View style={styles.list}>
          {rows.length === 0 && <Text style={styles.empty}>{t("avisos.sin_alertas")}</Text>}
          {rows.map((a, i) => {
            const look = LOOK[a.tipo] ?? LOOK.temporada;
            return (
              <View key={a.id} style={[styles.row, i > 0 && styles.divider, a.nuevo && styles.isNew]}>
                <View style={[styles.icon, { backgroundColor: look.bg }]}>
                  <Ionicons name={look.icon} size={26} color={look.color} />
                </View>
                <View style={{ flex: 1, gap: 2 }}>
                  <View style={styles.head}>
                    <Text style={styles.rowTitle}>{alertTitle(a, t)}</Text>
                    <Text style={styles.when}>{alertWhen(a, t)}</Text>
                  </View>
                  {alertDetail(a, t) ? <Text style={styles.detail}>{alertDetail(a, t)}</Text> : null}
                  {a.nuevo && <Text style={styles.newTag}>{t("avisos.nuevo")}</Text>}
                </View>
              </View>
            );
          })}
        </View>
        <Text style={styles.section}>{t("avisos.recordatorios")}</Text>
        <View style={styles.list}>
          <Text style={styles.empty}>{t("avisos.sin_recordatorios")}</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: Colors.paper },
  status: { paddingHorizontal: Spacing.gutter, paddingVertical: 4 },
  back: { flexDirection: "row", alignItems: "center", minHeight: 56, gap: 4 },
  backText: { ...Typography.label, color: Colors.ink },
  wall: { padding: Spacing.gutter, gap: 12, paddingBottom: 32 },
  title: { ...Typography.headline, color: Colors.ink },
  section: { ...Typography.title, fontSize: 22, color: Colors.ink, paddingTop: 6 },
  list: { borderWidth: 1, borderColor: Colors.line, borderRadius: Radius.card, overflow: "hidden" },
  row: { flexDirection: "row", gap: 12, padding: 14, alignItems: "flex-start" },
  divider: { borderTopWidth: 1, borderTopColor: Colors.line },
  isNew: { backgroundColor: Colors.fieldSoft },
  icon: { width: 48, height: 48, borderRadius: 24, alignItems: "center", justifyContent: "center" },
  head: { flexDirection: "row", justifyContent: "space-between", gap: 8, flexWrap: "wrap" },
  rowTitle: { ...Typography.label, fontSize: 19, color: Colors.ink, flexShrink: 1 },
  when: { ...Typography.meta, color: Colors.ink2 },
  detail: { ...Typography.body, fontSize: 17, color: Colors.ink2 },
  newTag: { ...Typography.meta, color: Colors.fieldDeep },
  empty: { ...Typography.body, fontSize: 17, color: Colors.ink2, padding: 14 },
});
