import { useEffect, useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import Svg, { Circle, Path, Rect } from "react-native-svg";
import { useTranslation } from "react-i18next";
import { Colors, Radius, Spacing, Touch, Typography } from "../../constants/Theme";
import { useFarm, useOffline } from "../../src/offline/provider";
import mockMap from "../../src/offline/fixtures/mapa.json";
import { fetchZoneMap, MapCache } from "../../src/zone/fetch";
import { floodMarks, historyItems, notice, projectCells } from "../../src/zone/map";
import { newReport, reportTypes, type ReportType } from "../../src/zone/report";
import { zones } from "../../src/farm/zones";
import { shortDate } from "../../src/ui/dates";
import { Sheet } from "../../src/ui/Sheet";

const VIEW = { width: 340, height: 520 };
const PARCELS = [
  [10, 14, 120, 70], [140, 10, 80, 60], [234, 14, 96, 70], [14, 96, 90, 80], [140, 80, 80, 96],
  [230, 96, 102, 64], [8, 190, 104, 70], [240, 172, 92, 72], [16, 272, 100, 72], [128, 272, 92, 84],
  [232, 256, 100, 62], [10, 356, 104, 52], [248, 408, 84, 44], [236, 462, 96, 50], [140, 456, 86, 56],
] as const;
type Icon = keyof typeof Ionicons.glyphMap;
const EVENT_ICON: Record<string, { icon: Icon; color: string; bg: string }> = {
  sin_agua: { icon: "water-outline", color: Colors.nowater, bg: Colors.nowaterSoft },
  helada: { icon: "snow-outline", color: Colors.frost, bg: Colors.frostSoft },
  granizo: { icon: "thunderstorm-outline", color: Colors.ink2, bg: Colors.paper2 },
  inundacion: { icon: "water", color: Colors.water, bg: Colors.waterSoft },
  plaga: { icon: "bug-outline", color: Colors.dry, bg: Colors.drySoft },
  sequia: { icon: "sunny-outline", color: Colors.dry, bg: Colors.drySoft },
  represa_baja: { icon: "water-outline", color: Colors.dry, bg: Colors.drySoft },
};
const API_URL = process.env.EXPO_PUBLIC_API_URL?.trim().replace(/\/$/, "");

function useZoneMap(zone: string) {
  const { client } = useOffline();
  const [map, setMap] = useState<unknown>(null);
  useEffect(() => {
    let active = true;
    const cache = new MapCache(client.store.db);
    void (async () => {
      const cached = await cache.read(zone);
      if (active && cached) setMap(cached);
      const fresh = API_URL ? await fetchZoneMap(API_URL, zone) : mockMap;
      if (!fresh) return;
      await cache.save(zone, fresh);
      if (active) setMap(fresh);
    })();
    return () => {
      active = false;
    };
  }, [client, zone]);
  return map;
}

export default function MiZonaScreen() {
  const { t } = useTranslation();
  const { client, zone, data } = useOffline();
  const { farm } = useFarm();
  const map = useZoneMap(zone);
  const [reporting, setReporting] = useState(false);
  const [history, setHistory] = useState(false);
  const [event, setEvent] = useState<ReportType | null>(null);
  const [saved, setSaved] = useState(false);
  const center = farm?.parcela ?? zones.find((z) => z.id === zone) ?? { lat: 0, lon: 0 };
  const cells = projectCells(map, center, VIEW);
  const floods = floodMarks(map, center, VIEW);
  const news = notice(map);
  const items = historyItems(data?.historial_zona);

  const send = async () => {
    if (!event) return;
    await client.outbox.enqueue(newReport(event, zone, farm?.parcela));
    void client.outbox.flush().catch(() => undefined);
    setReporting(false);
    setEvent(null);
    setSaved(true);
    setTimeout(() => setSaved(false), 4000);
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.wall}>
      <View style={styles.map} accessibilityLabel={t("zona.titulo")}>
        <Svg viewBox={`0 0 ${VIEW.width} ${VIEW.height}`} preserveAspectRatio="xMidYMid slice" style={StyleSheet.absoluteFill}>
          <Rect width={VIEW.width} height={VIEW.height} fill="#EEF3EC" />
          {PARCELS.map(([x, y, w, h], i) => (
            <Rect key={i} x={x} y={y} width={w} height={h} rx={6} fill={Colors.paper} stroke="#DCE6DB" />
          ))}
          {cells.map((c, i) => (
            <Rect key={i} x={c.x} y={c.y} width={c.w} height={c.h} rx={6} fill={Colors.nowater} fillOpacity={0.14} stroke={Colors.nowater} strokeWidth={2} />
          ))}
          {floods.map((f, i) => (
            <Circle key={i} cx={f.cx} cy={f.cy} r={28} fill={Colors.water} fillOpacity={0.18} stroke={Colors.water} strokeWidth={2} />
          ))}
          <Path d="M-10 500 C 70 470, 110 420, 180 400 S 290 372, 350 362" stroke={Colors.water} strokeWidth={6} fill="none" strokeLinecap="round" />
          <Circle cx={VIEW.width / 2} cy={VIEW.height / 2} r={26} fill={Colors.field} fillOpacity={0.16} />
          <Circle cx={VIEW.width / 2} cy={VIEW.height / 2} r={13} fill={Colors.field} stroke={Colors.paper} strokeWidth={4} />
        </Svg>
        <View style={styles.legend} pointerEvents="none">
          <Legend color={Colors.nowater} bg="#FBE3E0" label={t("zona.leyenda.sin_agua")} />
          <Legend color={Colors.water} bg="#D3E1F3" label={t("zona.leyenda.inunda")} />
          <Legend color={Colors.field} bg="#D2E7D8" label={t("zona.leyenda.parcela")} />
        </View>
      </View>
      {news && (
        <View style={styles.notice}>
          <Ionicons name="water-outline" size={30} color={Colors.nowater} />
          <View style={{ flex: 1 }}>
            <Text style={styles.noticeText}>{t("zona.vecinos", { count: news.vecinos })}</Text>
            <Text style={styles.noticeSub}>
              {news.direccion ? t("zona.donde", { direccion: news.direccion }) : t("zona.esta_semana")}
            </Text>
          </View>
        </View>
      )}
      {saved && (
        <View style={styles.saved} accessibilityLiveRegion="polite">
          <Ionicons name="checkmark-circle" size={24} color={Colors.field} />
          <Text style={styles.savedText}>{t("zona.guardado")}</Text>
        </View>
      )}
      <View style={styles.row}>
        <Pressable accessibilityRole="button" onPress={() => setReporting(true)} style={[styles.btn, styles.primary]}>
          <Ionicons name="alert-circle-outline" size={24} color={Colors.paper} />
          <Text style={[styles.btnText, { color: Colors.paper }]}>{t("zona.avisar")}</Text>
        </Pressable>
        <Pressable accessibilityRole="button" onPress={() => setHistory(true)} style={[styles.btn, styles.ghost]}>
          <Ionicons name="calendar-outline" size={24} color={Colors.fieldDeep} />
          <Text style={[styles.btnText, { color: Colors.fieldDeep }]}>{t("zona.historial")}</Text>
        </Pressable>
      </View>

      <Sheet visible={reporting} title={t("zona.avisar")} closeLabel={t("comun.cerrar")} onClose={() => setReporting(false)}>
        <Text style={styles.question}>{t("zona.que_paso")}</Text>
        <View style={styles.events}>
          {reportTypes.map((tipo) => {
            const on = tipo === event;
            const look = EVENT_ICON[tipo];
            return (
              <Pressable
                key={tipo}
                accessibilityRole="radio"
                accessibilityState={{ selected: on }}
                onPress={() => setEvent(tipo)}
                style={[styles.event, on && styles.eventOn]}
              >
                <Ionicons name={look.icon} size={26} color={on ? Colors.paper : look.color} />
                <Text style={[styles.eventText, on && { color: Colors.paper }]}>{t(`zona.evento.${tipo}`)}</Text>
              </Pressable>
            );
          })}
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityState={{ disabled: !event }}
          disabled={!event}
          onPress={() => void send()}
          style={[styles.btn, styles.primary, !event && styles.disabled]}
        >
          <Ionicons name="checkmark" size={24} color={Colors.paper} />
          <Text style={[styles.btnText, { color: Colors.paper }]}>{t("zona.enviar")}</Text>
        </Pressable>
      </Sheet>

      <Sheet visible={history} title={t("zona.historial")} closeLabel={t("comun.cerrar")} onClose={() => setHistory(false)}>
        {items.length === 0 && <Text style={styles.noticeSub}>{t("zona.sin_historial")}</Text>}
        {items.map((item, i) => {
          const look = EVENT_ICON[item.tipo] ?? EVENT_ICON.granizo;
          const title =
            item.nivel_pct != null
              ? t("zona.represa_nivel", { nivel: Math.round(item.nivel_pct) })
              : t(`zona.hecho.${item.tipo}`, { defaultValue: t("zona.hecho.otro") });
          return (
            <View key={`${item.fecha}-${i}`} style={styles.histRow}>
              <View style={[styles.histIcon, { backgroundColor: look.bg }]}>
                <Ionicons name={look.icon} size={24} color={look.color} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.histDate}>{`${shortDate(item.fecha)} ${item.fecha.slice(0, 4)}`}</Text>
                <Text style={styles.histTitle}>{title}</Text>
                {item.descripcion ? <Text style={styles.histText}>{item.descripcion}</Text> : null}
              </View>
            </View>
          );
        })}
      </Sheet>
    </ScrollView>
  );
}

function Legend({ color, bg, label }: { color: string; bg: string; label: string }) {
  return (
    <View style={styles.legendRow}>
      <View style={[styles.swatch, { backgroundColor: bg, borderColor: color }]} />
      <Text style={styles.legendText}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: Colors.paper },
  wall: { padding: Spacing.gutter, gap: 12, paddingBottom: 32 },
  map: {
    height: 440,
    borderRadius: Radius.card,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: Colors.line,
    backgroundColor: "#EEF3EC",
  },
  legend: {
    position: "absolute",
    left: 10,
    bottom: 10,
    gap: 4,
    padding: 10,
    borderRadius: 12,
    backgroundColor: "rgba(255,255,255,0.95)",
  },
  legendRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  swatch: { width: 18, height: 18, borderRadius: 4, borderWidth: 2 },
  legendText: { ...Typography.meta, fontSize: 16, color: Colors.ink },
  notice: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 14,
    borderRadius: Radius.card,
    backgroundColor: Colors.nowaterSoft,
  },
  noticeText: { ...Typography.label, fontSize: 19, color: Colors.nowater },
  noticeSub: { ...Typography.body, fontSize: 17, color: Colors.ink2 },
  saved: { flexDirection: "row", alignItems: "center", gap: 8 },
  savedText: { ...Typography.label, color: Colors.fieldDeep, flexShrink: 1 },
  row: { flexDirection: "row", gap: 8 },
  btn: {
    flex: 1,
    minHeight: Touch.buttonHeight,
    borderRadius: Radius.btn,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  primary: { backgroundColor: Colors.field },
  ghost: { backgroundColor: Colors.fieldSoft },
  disabled: { opacity: 0.4 },
  btnText: { ...Typography.label, fontSize: 19 },
  question: { ...Typography.title, fontSize: 22, color: Colors.ink },
  events: { flexDirection: "row", flexWrap: "wrap", gap: 8, paddingBottom: 8 },
  event: {
    flexBasis: "48%",
    flexGrow: 1,
    minHeight: 64,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.line,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingHorizontal: 8,
  },
  eventOn: { backgroundColor: Colors.field, borderColor: Colors.field },
  eventText: { ...Typography.label, fontSize: 18, color: Colors.ink },
  histRow: { flexDirection: "row", gap: 12, paddingVertical: 8 },
  histIcon: { width: 48, height: 48, borderRadius: 24, alignItems: "center", justifyContent: "center" },
  histDate: { ...Typography.meta, color: Colors.ink2 },
  histTitle: { ...Typography.label, fontSize: 19, color: Colors.ink },
  histText: { ...Typography.body, fontSize: 17, color: Colors.ink2 },
});
