import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";
import { Colors, Radius, Spacing, Typography } from "../../constants/Theme";
import { useOffline } from "../../src/offline/provider";
import { alertStrip, dayIcon, pickToday, rainWord, reservoirStrip, type DayIcon, type Today } from "../../src/today/today";
import { speak } from "../../src/today/speak";
import { MyCropsList } from "../../src/mycrops/MyCropsList";
import { laPazToday, longDate, weekday } from "../../src/ui/dates";

const ICONS: Record<DayIcon, { name: keyof typeof Ionicons.glyphMap; color: string }> = {
  granizo: { name: "thunderstorm-outline", color: Colors.ink2 },
  helada: { name: "snow-outline", color: Colors.frost },
  lluvia: { name: "rainy-outline", color: Colors.water },
  sol: { name: "sunny-outline", color: Colors.dry },
};

const capital = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

export default function HoyScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { data } = useOffline();
  const fecha = laPazToday();
  const day = pickToday(data, fecha);
  const alert = alertStrip(data?.alertas);
  const reservoir = reservoirStrip(data?.represa);

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.wall}>
      {alert && (
        <View style={styles.alert} accessibilityRole="alert">
          <Ionicons
            name={alert.tipo === "represa_baja" ? "water-outline" : "snow-outline"}
            size={28}
            color={Colors.frost}
          />
          <Text style={styles.alertText}>
            {"nivel_pct" in alert
              ? t("hoy.alerta.represa_baja", { nivel: alert.nivel_pct })
              : t(`hoy.alerta.${alert.tipo}`, { dia: weekday(alert.fecha) }) +
                (alert.tmin == null ? "" : ` · ${alert.tmin} °C`)}
          </Text>
        </View>
      )}
      {day ? <DayCard day={day} /> : <Text style={styles.empty}>{t("hoy.sin_datos")}</Text>}
      <View style={styles.sectionHead}>
        <Text style={styles.sectionTitle}>{t("hoy.mis_cultivos")}</Text>
        <Pressable accessibilityRole="button" onPress={() => router.push("/sembrar")} style={styles.add}>
          <Ionicons name="add" size={22} color={Colors.fieldDeep} />
          <Text style={styles.addText}>{t("hoy.agregar")}</Text>
        </Pressable>
      </View>
      <MyCropsList emptyText={t("hoy.sin_cultivos")} />
      {reservoir && (
        <View style={styles.water}>
          <Ionicons name="water-outline" size={26} color={Colors.water} />
          <View style={{ flex: 1 }}>
            <Text style={styles.waterText}>{t("hoy.represa", { nivel: Math.round(reservoir.nivel_pct) })}</Text>
            <View style={styles.level}>
              <View style={[styles.levelFill, { width: `${Math.min(100, reservoir.nivel_pct)}%` }]} />
            </View>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

function DayCard({ day }: { day: Today }) {
  const { t } = useTranslation();
  const icon = dayIcon(day);
  const frost = day.tmin < 0;
  const sky = t(`hoy.cielo.${icon}`);
  const rain = t(`hoy.lluvia.${rainWord(day.pmm)}`);
  const summary = t("hoy.resumen", {
    dia: capital(weekday(day.fecha)),
    fecha: longDate(day.fecha),
    cielo: sky,
    lluvia: rain.toLowerCase(),
    tmax: day.tmax,
    tmin: day.tmin,
  });
  return (
    <View style={[styles.day, frost && styles.dayFrost]}>
      <View style={styles.top}>
        <View>
          <Text style={styles.dayName}>{t("hoy.titulo")}</Text>
          <Text style={styles.dayDate}>{longDate(day.fecha)}</Text>
        </View>
        <Pressable accessibilityRole="button" onPress={() => speak(summary)} style={styles.speak}>
          <Ionicons name="volume-high-outline" size={22} color={Colors.fieldDeep} />
          <Text style={styles.speakText}>{t("hoy.escuchar")}</Text>
        </Pressable>
      </View>
      <View style={styles.mid}>
        <Ionicons name={ICONS[icon].name} size={104} color={ICONS[icon].color} />
        <View style={styles.temps}>
          <Text style={styles.tmax}>{day.tmax}°</Text>
          <Text style={styles.tmin}>{t("hoy.minima", { t: day.tmin })}</Text>
        </View>
      </View>
      <View style={[styles.bottom, frost && styles.bottomFrost]}>
        <Text style={styles.sky}>{sky}</Text>
        <View style={{ alignItems: "flex-end", flexShrink: 1 }}>
          <Text style={styles.rain}>{rain}</Text>
          {frost && <Text style={styles.warn}>{t("hoy.aviso_helada")}</Text>}
          {!frost && day.granizo && <Text style={styles.warn}>{t("hoy.aviso_granizo")}</Text>}
          {day.proyeccion && <Text style={styles.approx}>{t("hoy.proyeccion")}</Text>}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: Colors.paper },
  wall: { padding: Spacing.gutter, gap: 12, paddingBottom: 32 },
  alert: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    minHeight: 56,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: Radius.card,
    backgroundColor: Colors.frostSoft,
  },
  alertText: { ...Typography.label, fontSize: 19, color: Colors.ink, flexShrink: 1 },
  day: {
    gap: 6,
    paddingVertical: 16,
    paddingHorizontal: 20,
    borderRadius: Radius.sheet,
    borderWidth: 1,
    borderColor: Colors.line,
    backgroundColor: Colors.paper,
  },
  dayFrost: { backgroundColor: Colors.frostSoft, borderColor: "#B6E0EA" },
  top: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: 10 },
  dayName: { ...Typography.headline, fontSize: 24, color: Colors.ink },
  dayDate: { ...Typography.label, color: Colors.ink2 },
  speak: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    minHeight: 52,
    paddingHorizontal: 16,
    borderRadius: Radius.pill,
    backgroundColor: Colors.fieldSoft,
  },
  speakText: { ...Typography.label, color: Colors.fieldDeep },
  mid: { flexDirection: "row", alignItems: "center", justifyContent: "space-around", paddingVertical: 8 },
  temps: { alignItems: "center" },
  tmax: { fontFamily: Typography.headline.fontFamily, fontSize: 68, lineHeight: 72, color: Colors.ink, letterSpacing: -2 },
  tmin: { ...Typography.title, color: Colors.ink2 },
  bottom: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    gap: 10,
    borderTopWidth: 1,
    borderTopColor: Colors.line,
    paddingTop: 12,
  },
  bottomFrost: { borderTopColor: "#B6E0EA" },
  sky: { ...Typography.headline, color: Colors.ink },
  rain: { ...Typography.body, color: Colors.ink2, textAlign: "right" },
  warn: { ...Typography.label, fontSize: 19, color: Colors.frost, textAlign: "right" },
  approx: { ...Typography.meta, color: Colors.ink2, textAlign: "right" },
  empty: { ...Typography.body, color: Colors.ink2 },
  sectionHead: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: 4 },
  sectionTitle: { ...Typography.title, color: Colors.ink },
  add: { flexDirection: "row", alignItems: "center", gap: 4, minHeight: 56, paddingHorizontal: 8 },
  addText: { ...Typography.label, color: Colors.fieldDeep },
  water: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    minHeight: 68,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.line,
  },
  waterText: { ...Typography.label, fontSize: 19, color: Colors.ink },
  level: { height: 8, borderRadius: 4, backgroundColor: Colors.paper2, marginTop: 4, overflow: "hidden" },
  levelFill: { height: "100%", backgroundColor: Colors.water },
});
