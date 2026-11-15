import { useEffect, useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";
import { Colors, Radius, Spacing, Typography } from "../../constants/Theme";
import {
  buildWeeks,
  pastWeeks,
  monthsAhead,
  sourceLine,
  type MonthTile,
  type Week,
  type WeekTile,
} from "../../src/calendar/calendar";
import { useOffline } from "../../src/offline/provider";
import { dayIcon, rainWord, type DayIcon } from "../../src/today/today";
import { laPazToday, monthName, shortDate, weekday } from "../../src/ui/dates";
import { Sheet } from "../../src/ui/Sheet";
import { fetchHistory, HistoryCache } from "../../src/zone/fetch";
import type { MyCrop } from "../../src/farm/my-crops";
import { cropEvents } from "../../src/mycrops/mycrops";
import { MyCropSheet } from "../../src/mycrops/MyCropSheet";
import { cropName, useMyCrops } from "../../src/mycrops/use-my-crops";

type Icon = keyof typeof Ionicons.glyphMap;
const TILE: Record<WeekTile | MonthTile, { icon: Icon; bg: string; fg: string }> = {
  granizo: { icon: "thunderstorm-outline", bg: "#E9ECEE", fg: "#2B3A33" },
  helada: { icon: "snow-outline", bg: Colors.frostSoft, fg: Colors.frost },
  lluvia_fuerte: { icon: "rainy", bg: Colors.water, fg: Colors.paper },
  lluvia: { icon: "rainy-outline", bg: Colors.waterSoft, fg: Colors.water },
  poca_lluvia: { icon: "partly-sunny-outline", bg: Colors.waterSoft, fg: Colors.water },
  sin_lluvia: { icon: "sunny-outline", bg: Colors.drySoft, fg: Colors.dry },
  seco: { icon: "sunny-outline", bg: Colors.drySoft, fg: Colors.dry },
  sin_datos: { icon: "help-outline", bg: Colors.paper2, fg: Colors.ink2 },
};
const DAY_ICON: Record<DayIcon, { icon: Icon; color: string }> = {
  granizo: { icon: "thunderstorm-outline", color: Colors.ink2 },
  helada: { icon: "snow-outline", color: Colors.frost },
  lluvia: { icon: "rainy-outline", color: Colors.water },
  sol: { icon: "sunny-outline", color: Colors.dry },
};

const API_URL = process.env.EXPO_PUBLIC_API_URL?.trim().replace(/\/$/, "");
const PAST_DAYS = 28;

function shift(iso: string, n: number) {
  const date = new Date(`${iso}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + n);
  return date.toISOString().slice(0, 10);
}

function useHistory(zone: string, today: string) {
  const { client } = useOffline();
  const [history, setHistory] = useState<unknown>(null);
  useEffect(() => {
    let active = true;
    const cache = new HistoryCache(client.store.db);
    void (async () => {
      const cached = await cache.read(zone);
      if (active && cached) setHistory(cached);
      if (!API_URL) return;
      const fresh = await fetchHistory(API_URL, zone, shift(today, -PAST_DAYS), shift(today, -1));
      if (!fresh) return;
      await cache.save(zone, fresh);
      if (active) setHistory(fresh);
    })();
    return () => {
      active = false;
    };
  }, [client, zone, today]);
  return history;
}

const capital = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);
const range = (w: Week) => `${Number(w.inicio.slice(8))} – ${shortDate(w.fin)}`;

export default function CalendarioScreen() {
  const { t } = useTranslation();
  const { data, zone } = useOffline();
  const today = laPazToday();
  const [open, setOpen] = useState<Week | null>(null);
  const [openPast, setOpenPast] = useState(false);
  const [showPast, setShowPast] = useState(false);
  const history = useHistory(zone, today);
  const past = pastWeeks(history, today).filter((w) => w.dias.length > 0);
  const historySource = sourceLine((history as { fuente?: string[] } | null)?.fuente);
  const [months, setMonths] = useState(false);
  const [crop, setCrop] = useState<MyCrop | null>(null);
  const { crops } = useMyCrops();
  const weeks = buildWeeks(data, today);
  const ahead = monthsAhead(data?.climatologia, today);
  const clima = data?.climatologia as { fuente?: string[]; periodo?: { power?: string } } | undefined;

  const weekSources = (w: Week) => {
    const short = (data?.corto_plazo as { fuente?: string[] } | undefined)?.fuente ?? [];
    const projection = (data?.forecast as { fuente?: string[] } | undefined)?.fuente ?? [];
    const codes = new Set([
      ...(w.dias.some((d) => !d.proyeccion) ? short : []),
      ...(w.dias.some((d) => d.proyeccion) ? projection : []),
    ]);
    return sourceLine([...codes]);
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.wall}>
      <Text style={styles.title}>{t("calendario.titulo")}</Text>
      <Text style={styles.section}>{t("calendario.proximas")}</Text>
      <View style={styles.list}>
        {weeks.flatMap((w, k) => [
          <Pressable
            key={w.inicio}
            accessibilityRole="button"
            onPress={() => setOpen(w)}
            style={({ pressed }) => [styles.item, k === 0 && styles.now, k > 0 && styles.divider, pressed && styles.pressed]}
          >
            <Tile tile={w.tile} label={t(`calendario.semana.${w.tile}`)} />
            <View style={styles.body}>
              <View style={styles.top}>
                <Text style={styles.range}>{range(w)}</Text>
                {k === 0 && <Text style={styles.tag}>{t("calendario.esta_semana")}</Text>}
              </View>
              {w.tile !== "sin_datos" && (
                <View style={styles.wx}>
                  <Text style={[styles.wxText, w.pmm >= 4 && styles.wet]}>
                    {capital(t(`hoy.lluvia.${rainWord(w.pmm)}`).toLowerCase())}
                  </Text>
                  {w.helada && <Text style={[styles.wxText, styles.frost]}>{t("calendario.helada_el", { dia: weekday(w.helada) })}</Text>}
                  {w.granizo && <Text style={styles.wxText}>{t("calendario.granizo_el", { dia: weekday(w.granizo) })}</Text>}
                </View>
              )}
              {w.lejos && <Text style={styles.far}>{t("calendario.lejos")}</Text>}
            </View>
            <Ionicons name="chevron-forward" size={24} color={Colors.field} />
          </Pressable>,
          ...cropEvents(crops, w.inicio, w.fin).map((e) => (
            <Pressable
              key={`${e.crop.id}-${e.tipo}`}
              accessibilityRole="button"
              onPress={() => setCrop(e.crop)}
              style={({ pressed }) => [styles.item, styles.divider, pressed && styles.pressed]}
            >
              <View style={styles.eventTile}>
                <Ionicons name={e.tipo === "siembra" ? "leaf-outline" : "checkmark"} size={28} color={Colors.field} />
                <Text style={styles.eventKind}>{t(`cultivos.${e.tipo}`)}</Text>
              </View>
              <View style={styles.body}>
                <Text style={styles.range}>{`${capital(weekday(e.fecha))} ${shortDate(e.fecha)}`}</Text>
                <Text style={[styles.wxText, { color: Colors.fieldDeep }]}>
                  {t(`cultivos.${e.tipo}_de`, { cultivo_min: cropName(data, e.crop.crop_id).toLowerCase() })}
                </Text>
              </View>
              <Ionicons name="chevron-forward" size={24} color={Colors.field} />
            </Pressable>
          )),
        ])}
      </View>
      <MyCropSheet crop={crop} onClose={() => setCrop(null)} />
      {past.length > 0 && (
        <Pressable accessibilityRole="button" onPress={() => setShowPast(!showPast)} style={styles.more}>
          <Ionicons name={showPast ? "chevron-down" : "chevron-back"} size={22} color={Colors.ink} />
          <Text style={styles.moreText}>{showPast ? t("calendario.ocultar_pasadas") : t("calendario.ver_pasadas")}</Text>
        </Pressable>
      )}
      {showPast && (
        <View style={styles.list}>
          {past.map((w, k) => (
            <Pressable
              key={w.inicio}
              accessibilityRole="button"
              onPress={() => {
                setOpenPast(true);
                setOpen(w);
              }}
              style={({ pressed }) => [styles.item, k > 0 && styles.divider, styles.pastItem, pressed && styles.pressed]}
            >
              <Tile tile={w.tile} label={t(`calendario.semana.${w.tile}`)} />
              <View style={styles.body}>
                <Text style={styles.range}>{range(w)}</Text>
                <View style={styles.wx}>
                  <Text style={[styles.wxText, w.pmm >= 4 && styles.wet]}>
                    {capital(t(`hoy.lluvia.${rainWord(w.pmm)}`).toLowerCase())}
                  </Text>
                  {w.helada && <Text style={[styles.wxText, styles.frost]}>{t("calendario.helada_el", { dia: weekday(w.helada) })}</Text>}
                </View>
              </View>
              <Ionicons name="chevron-forward" size={24} color={Colors.field} />
            </Pressable>
          ))}
        </View>
      )}
      {ahead.length > 0 && (
        <Pressable accessibilityRole="button" onPress={() => setMonths(true)} style={styles.more}>
          <Text style={styles.moreText}>{t("calendario.ver_meses")}</Text>
          <Ionicons name="chevron-forward" size={22} color={Colors.ink} />
        </Pressable>
      )}

      <Sheet
        visible={open !== null}
        title={open ? range(open) : ""}
        subtitle={openPast ? t("calendario.medido") : open?.lejos ? t("calendario.lejos") : t("calendario.pronostico")}
        closeLabel={t("comun.cerrar")}
        onClose={() => {
          setOpen(null);
          setOpenPast(false);
        }}
      >
        {open?.dias.map((d) => {
          const icon = dayIcon(d);
          return (
            <View key={d.fecha} style={[styles.dayRow, d.tmin < 0 && styles.dayFrost]}>
              <View style={{ width: 96 }}>
                <Text style={styles.dayName}>{capital(weekday(d.fecha))}</Text>
                <Text style={styles.dayDate}>{shortDate(d.fecha)}</Text>
              </View>
              <Ionicons name={DAY_ICON[icon].icon} size={32} color={DAY_ICON[icon].color} />
              <View style={{ flex: 1 }}>
                <Text style={styles.dayWord}>{t(`hoy.cielo.${icon}`)}</Text>
                <Text style={styles.dayRain}>{t(`hoy.lluvia.${rainWord(d.pmm)}`)}</Text>
                {d.tmin < 0 && <Text style={styles.warn}>{t("hoy.aviso_helada")}</Text>}
                {d.tmin >= 0 && d.granizo && <Text style={styles.warn}>{t("hoy.aviso_granizo")}</Text>}
              </View>
              <View style={{ alignItems: "flex-end" }}>
                <Text style={styles.dayMax}>{d.tmax}°</Text>
                <Text style={styles.dayRain}>{d.tmin}°</Text>
              </View>
            </View>
          );
        })}
        {open && <Source text={t("calendario.fuente", { fuentes: openPast ? historySource : weekSources(open) })} />}
      </Sheet>

      <Sheet
        visible={months}
        title={t("calendario.meses_titulo")}
        subtitle={t("calendario.meses_nota")}
        closeLabel={t("comun.cerrar")}
        onClose={() => setMonths(false)}
      >
        {ahead.map((m) => (
          <View key={m.mes} style={styles.month}>
            <Tile tile={m.tile} label={t(`calendario.mes.${m.tile}`)} />
            <View style={styles.body}>
              <Text style={styles.range}>{capital(monthName(m.mes))}</Text>
              <Text style={[styles.wxText, m.helada && styles.frost]}>
                {m.helada ? capital(t("calendario.riesgo_helada")) : t("calendario.sin_riesgos")}
              </Text>
            </View>
          </View>
        ))}
        <Source
          text={t("calendario.clima_tipico", {
            fuentes: sourceLine(clima?.fuente),
            periodo: clima?.periodo?.power ?? "",
          })}
        />
      </Sheet>
    </ScrollView>
  );
}

function Tile({ tile, label }: { tile: WeekTile | MonthTile; label: string }) {
  const style = TILE[tile];
  return (
    <View style={[styles.tile, { backgroundColor: style.bg }]}>
      <Ionicons name={style.icon} size={40} color={style.fg} />
      <Text style={[styles.tileText, { color: style.fg }]}>{label}</Text>
    </View>
  );
}

function Source({ text }: { text: string }) {
  return (
    <View style={styles.source}>
      <Ionicons name="information-circle-outline" size={20} color={Colors.ink2} />
      <Text style={styles.sourceText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: Colors.paper },
  wall: { padding: Spacing.gutter, gap: 12, paddingBottom: 32 },
  title: { ...Typography.headline, color: Colors.ink },
  section: { ...Typography.title, fontSize: 22, color: Colors.ink, paddingTop: 6 },
  list: { borderWidth: 1, borderColor: Colors.line, borderRadius: Radius.card, overflow: "hidden" },
  item: { flexDirection: "row", gap: 12, padding: 14, alignItems: "center", backgroundColor: Colors.paper },
  divider: { borderTopWidth: 1, borderTopColor: Colors.line },
  now: { backgroundColor: Colors.fieldSoft },
  pressed: { backgroundColor: Colors.paper2 },
  tile: {
    width: 92,
    minHeight: 104,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    padding: 6,
  },
  tileText: { ...Typography.meta, textAlign: "center" },
  body: { flex: 1, gap: 6 },
  top: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: 8 },
  range: { ...Typography.title, fontSize: 21, color: Colors.ink },
  tag: {
    ...Typography.meta,
    color: Colors.paper,
    backgroundColor: Colors.ink,
    borderRadius: Radius.pill,
    overflow: "hidden",
    paddingHorizontal: 9,
    paddingVertical: 3,
  },
  wx: { flexDirection: "row", flexWrap: "wrap", gap: 12 },
  wxText: { ...Typography.label, fontSize: 18, color: Colors.ink2 },
  wet: { color: Colors.water },
  frost: { color: Colors.frost },
  far: { ...Typography.meta, color: Colors.ink2 },
  more: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    minHeight: 56,
    borderRadius: Radius.pill,
    backgroundColor: Colors.paper2,
  },
  moreText: { ...Typography.label, fontSize: 18, color: Colors.ink },
  dayRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 12,
    borderRadius: 14,
    backgroundColor: Colors.paper2,
  },
  dayFrost: { backgroundColor: Colors.frostSoft },
  dayName: { ...Typography.label, fontSize: 18, color: Colors.ink },
  dayDate: { ...Typography.meta, color: Colors.ink2 },
  dayWord: { ...Typography.label, fontSize: 18, color: Colors.ink },
  dayRain: { ...Typography.meta, fontSize: 16, color: Colors.ink2 },
  dayMax: { ...Typography.title, color: Colors.ink },
  warn: { ...Typography.meta, color: Colors.frost },
  month: { flexDirection: "row", gap: 12, alignItems: "center", paddingVertical: 6 },
  source: { flexDirection: "row", gap: 8, alignItems: "center", paddingTop: 12 },
  pastItem: { opacity: 0.85 },
  eventTile: { width: 92, alignItems: "center", justifyContent: "center", gap: 2 },
  eventKind: { ...Typography.meta, color: Colors.fieldDeep },
  sourceText: { ...Typography.meta, color: Colors.ink2, flexShrink: 1 },
});
