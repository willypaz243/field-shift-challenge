import { useEffect, useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";
import { Colors, Radius, Spacing, Touch, Typography } from "../../constants/Theme";
import { useFarm, useOffline } from "../../src/offline/provider";
import mockMap from "../../src/offline/fixtures/mapa.json";
import { fetchZoneMap, MapCache } from "../../src/zone/fetch";
import { historyItems, notice } from "../../src/zone/map";
import { ZoneMap } from "../../src/ui/ZoneMap";
import { newReport, reportTypes, type ReportType } from "../../src/zone/report";
import { cleanupPhotos, takePhoto, type Photo } from "../../src/zone/photo";
import { zones } from "../../src/farm/zones";
import { shortDate } from "../../src/ui/dates";
import { Sheet } from "../../src/ui/Sheet";

// Colours of the GAMC layers (from their WMS legends), so the legend matches the map.
const GAMC = { crecimiento: "#A2FF70", consolidado: "#FFA58E", drenaje: "#398BFF" };
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
  const [photo, setPhoto] = useState<Photo | null>(null);
  const [photoError, setPhotoError] = useState(false);
  const center = farm?.parcela ?? zones.find((z) => z.id === zone) ?? { lat: 0, lon: 0 };
  const news = notice(map);
  const items = historyItems(data?.historial_zona);

  const addPhoto = async () => {
    setPhotoError(false);
    const taken = await takePhoto().catch(() => "too_big" as const);
    if (taken === "too_big") setPhotoError(true);
    else if (taken) setPhoto(taken);
  };

  const send = async () => {
    if (!event) return;
    await client.outbox.enqueue(newReport(event, zone, farm?.parcela, new Date(), photo ?? undefined));
    void client.outbox
      .flush()
      .then(() => cleanupPhotos(client.store.db))
      .catch(() => undefined);
    setReporting(false);
    setEvent(null);
    setPhoto(null);
    setSaved(true);
    setTimeout(() => setSaved(false), 4000);
  };

  return (
    <View style={styles.screen}>
      <View style={styles.map}>
        <ZoneMap
          zoneId={zone}
          center={center}
          pin={farm?.parcela ?? center}
          layers={map}
          credit={t("comun.mapa_gamc")}
          accessibilityLabel={t("zona.titulo")}
          zoomLabels={{ in: t("zona.acercar"), out: t("zona.alejar") }}
        >
        </ZoneMap>
      </View>
      <View style={styles.legend}>
        <Legend color={Colors.nowater} bg="#FBE3E0" label={t("zona.leyenda.sin_agua")} />
        <Legend color={Colors.water} bg="#D3E1F3" label={t("zona.leyenda.inunda")} />
        <Legend color={Colors.field} bg="#D2E7D8" label={t("zona.leyenda.parcela")} />
        <Legend color="#7FCC5A" bg={GAMC.crecimiento} label={t("zona.leyenda.crecimiento")} />
        <Legend color="#E08A72" bg={GAMC.consolidado} label={t("zona.leyenda.consolidado")} />
        <Legend color={GAMC.drenaje} bg={GAMC.drenaje} label={t("zona.leyenda.rios")} />
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
          accessibilityState={{ selected: !!photo }}
          onPress={() => void addPhoto()}
          style={[styles.btn, styles.ghost, { flex: 0 }]}
        >
          <Ionicons name={photo ? "checkmark-circle" : "camera-outline"} size={24} color={Colors.fieldDeep} />
          <Text style={[styles.btnText, { color: Colors.fieldDeep }]}>{photo ? t("zona.foto_lista") : t("zona.foto")}</Text>
        </Pressable>
        {photoError && <Text style={styles.noticeSub}>{t("zona.foto_grande")}</Text>}
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
    </View>
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
  screen: { flex: 1, backgroundColor: Colors.paper, padding: Spacing.gutter, gap: 10 },
  map: {
    flex: 1,
    minHeight: 280,
    borderRadius: Radius.card,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: Colors.line,
    backgroundColor: "#EEF3EC",
  },
  legend: { flexDirection: "row", flexWrap: "wrap", columnGap: 14, rowGap: 4 },
  legendRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  swatch: { width: 16, height: 16, borderRadius: 4, borderWidth: 2 },
  legendText: { ...Typography.meta, fontSize: 17, color: Colors.ink },
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
