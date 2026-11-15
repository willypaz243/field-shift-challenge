import { useMemo, useRef, useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Image, PanResponder, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTranslation } from "react-i18next";
import { Colors, Radius, Spacing, Touch, Typography } from "../../constants/Theme";
import { sourceLine } from "../../src/calendar/calendar";
import { MyCrops } from "../../src/farm/my-crops";
import { notifyMyCrops } from "../../src/mycrops/use-my-crops";
import { useOffline } from "../../src/offline/provider";
import { windowsFor } from "../../src/scoring/local";
import type { Veredicto } from "../../src/scoring/scoring";
import { addDays, cycleDays, dayVerdicts, findCrop, monthGrid, scoreFrom } from "../../src/sow/sow";
import { cropImages } from "../../src/ui/crop-images";
import { laPazToday, monthName, shortDate } from "../../src/ui/dates";
import { Sheet } from "../../src/ui/Sheet";

type CatalogCrop = { nombre: string; agua?: { demanda?: string }; helada?: { tolerancia?: string } };
const VERDICT_LOOK: Record<Veredicto, { color: string; bg: string; icon: keyof typeof Ionicons.glyphMap }> = {
  bueno: { color: Colors.fieldDeep, bg: Colors.fieldSoft, icon: "checkmark-circle" },
  con_cuidado: { color: Colors.dry, bg: Colors.drySoft, icon: "alert-circle" },
  malo: { color: Colors.nowater, bg: Colors.nowaterSoft, icon: "close-circle" },
};

export default function CultivoScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { client, data } = useOffline();
  const today = laPazToday();
  const tomorrow = addDays(today, 1);
  const crop = findCrop(data, id) as (ReturnType<typeof findCrop> & CatalogCrop) | null;
  const verdicts = useMemo(() => dayVerdicts(data, id, today), [data, id, today]);
  const best = useMemo(() => windowsFor(data, id, today)[0], [data, id, today]);
  const now = scoreFrom(data, id, today, tomorrow);
  const [picking, setPicking] = useState(false);
  const [saved, setSaved] = useState<string | null>(null);
  const fuente = sourceLine((data?.forecast as { fuente?: string[] } | undefined)?.fuente);

  if (!crop) return null;
  const L = cycleDays(crop);

  const add = async (siembra: string) => {
    const cosecha = addDays(siembra, L);
    await new MyCrops(client.store.db).add({ crop_id: id, siembra, cosecha });
    notifyMyCrops();
    setPicking(false);
    setSaved(t("sembrar.agregado", { cultivo: crop.nombre, siembra: shortDate(siembra), cosecha: shortDate(cosecha) }));
  };

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.status}>
        <Pressable accessibilityRole="button" onPress={() => router.back()} style={styles.back}>
          <Ionicons name="chevron-back" size={24} color={Colors.ink} />
          <Text style={styles.backText}>{t("comun.atras")}</Text>
        </Pressable>
      </View>
      <ScrollView contentContainerStyle={styles.wall}>
        <Text style={styles.title}>{crop.nombre}</Text>
        {cropImages[id] && <Image source={cropImages[id]} style={styles.hero} resizeMode="cover" />}
        <View style={styles.facts}>
          <Fact icon="water-outline" label={t("sembrar.agua")} value={t(`sembrar.agua_nivel.${crop.agua?.demanda ?? "media"}`, { defaultValue: crop.agua?.demanda ?? "" })} />
          <Fact icon="snow-outline" label={t("sembrar.frio")} value={t(`sembrar.frio_nivel.${crop.helada?.tolerancia ?? "baja"}`)} />
        </View>
        {best ? (
          <View style={styles.two}>
            <Box label={t("sembrar.siembra")} value={shortDate(best.inicio)} />
            <Box label={t("sembrar.cosecha")} value={shortDate(best.fin)} />
          </View>
        ) : (
          <Text style={styles.body}>{t("sembrar.sin_datos")}</Text>
        )}
        {now && (
          <View style={[styles.now, { backgroundColor: VERDICT_LOOK[now.veredicto].bg }]}>
            <View style={styles.nowHead}>
              <Text style={styles.nowTitle}>{t("sembrar.si_ahora")}</Text>
              <View style={styles.verdict}>
                <Ionicons name={VERDICT_LOOK[now.veredicto].icon} size={22} color={VERDICT_LOOK[now.veredicto].color} />
                <Text style={[styles.verdictText, { color: VERDICT_LOOK[now.veredicto].color }]}>{t(`sembrar.veredicto.${now.veredicto}`)}</Text>
              </View>
            </View>
            {now.motivos.length === 0 ? (
              <Text style={styles.body}>{t("sembrar.bueno_motivo")}</Text>
            ) : (
              now.motivos.map((m) => (
                <Text key={m} style={styles.body}>
                  {t(`sembrar.motivo.${m}`)}
                </Text>
              ))
            )}
          </View>
        )}
        {saved && <Text style={styles.saved}>{saved}</Text>}
        {verdicts.size > 0 && (
          <Pressable accessibilityRole="button" onPress={() => setPicking(true)} style={styles.primary}>
            <Ionicons name="calendar-outline" size={24} color={Colors.paper} />
            <Text style={styles.primaryText}>{t("sembrar.elegir_fecha")}</Text>
          </Pressable>
        )}
        {fuente ? <Text style={styles.source}>{t("sembrar.fuente", { fuentes: fuente })}</Text> : null}
      </ScrollView>
      <Sheet visible={picking} title={t("sembrar.elegir_fecha")} subtitle={crop.nombre} closeLabel={t("comun.cerrar")} onClose={() => setPicking(false)}>
        <DatePicker today={today} first={tomorrow} cycle={L} verdicts={verdicts} onAdd={(d) => void add(d)}
          onPlan={(cosecha) => {
            setPicking(false);
            router.push({ pathname: "/rotar", params: { c: id, h: cosecha } });
          }}
        />
        {fuente ? <Text style={styles.source}>{t("sembrar.fuente", { fuentes: fuente })}</Text> : null}
      </Sheet>
    </SafeAreaView>
  );
}

function DatePicker({
  today,
  first,
  cycle,
  verdicts,
  onAdd,
  onPlan,
}: {
  today: string;
  first: string;
  cycle: number;
  verdicts: Map<string, Veredicto>;
  onAdd: (siembra: string) => void;
  onPlan: (cosecha: string) => void;
}) {
  const { t } = useTranslation();
  const [view, setView] = useState({ year: Number(today.slice(0, 4)), month: Number(today.slice(5, 7)) });
  const [start, setStart] = useState<string | null>(null);
  const shift = (step: number) =>
    setView((v) => {
      const m = v.month - 1 + step;
      return { year: v.year + Math.floor(m / 12), month: ((m % 12) + 12) % 12 + 1 };
    });
  const swipe = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, g) => Math.abs(g.dx) > 20 && Math.abs(g.dx) > Math.abs(g.dy),
      onPanResponderRelease: (_, g) => {
        if (Math.abs(g.dx) > 60) shift(g.dx < 0 ? 1 : -1);
      },
    }),
  ).current;
  const harvest = start ? addDays(start, cycle) : null;
  const verdict = start ? verdicts.get(start) : undefined;
  const weekdays = t("sembrar.semana").split(",");

  return (
    <View style={{ gap: 10 }}>
      <View style={styles.monthHead}>
        <Pressable accessibilityRole="button" accessibilityLabel={t("sembrar.mes_anterior")} onPress={() => shift(-1)} style={styles.arrow}>
          <Ionicons name="chevron-back" size={24} color={Colors.ink} />
        </Pressable>
        <Text style={styles.monthTitle}>{`${monthName(view.month).charAt(0).toUpperCase()}${monthName(view.month).slice(1)} ${view.year}`}</Text>
        <Pressable accessibilityRole="button" accessibilityLabel={t("sembrar.mes_siguiente")} onPress={() => shift(1)} style={styles.arrow}>
          <Ionicons name="chevron-forward" size={24} color={Colors.ink} />
        </Pressable>
      </View>
      <View style={styles.grid} {...swipe.panHandlers}>
        {weekdays.map((d, i) => (
          <Text key={`h${i}`} style={styles.weekday}>
            {d}
          </Text>
        ))}
        {monthGrid(view.year, view.month).map((day, i) => {
          if (!day) return <View key={i} style={styles.cell} />;
          const past = day < first;
          const v = verdicts.get(day);
          const inCrop = start && harvest && day >= start && day <= harvest;
          const isEdge = day === start || day === harvest;
          return (
            <View key={i} style={[styles.cell, inCrop && styles.band]}>
              <Pressable
                accessibilityRole="button"
                accessibilityState={{ disabled: past, selected: day === start }}
                disabled={past}
                onPress={() => setStart(day)}
                style={[
                  styles.day,
                  !past && v === "bueno" && styles.good,
                  !past && v === "malo" && styles.bad,
                  day === today && styles.today,
                  isEdge && styles.edge,
                ]}
              >
                <Text style={[styles.dayText, past && styles.pastText, isEdge && styles.edgeText]}>{Number(day.slice(8))}</Text>
              </Pressable>
            </View>
          );
        })}
      </View>
      <View style={styles.legend}>
        <Legend style={styles.good} label={t("sembrar.buenos")} />
        <Legend style={styles.bad} label={t("sembrar.malos")} />
        {start && <Legend style={styles.band} label={t("sembrar.tu_cultivo")} />}
      </View>
      {!start ? (
        <Text style={styles.body}>{t("sembrar.toca_dia")}</Text>
      ) : (
        <>
          <View style={[styles.result, { backgroundColor: VERDICT_LOOK[verdict ?? "con_cuidado"].bg }]}>
            <Text style={[styles.resultTitle, { color: VERDICT_LOOK[verdict ?? "con_cuidado"].color }]}>
              {verdict ? t(`sembrar.fecha.${verdict}`) : t("sembrar.fecha.con_cuidado")}
            </Text>
            <Text style={styles.body}>{verdict ? t(`sembrar.fecha_detalle.${verdict}`) : t("sembrar.sin_fecha")}</Text>
          </View>
          <View style={styles.two}>
            <Box label={t("sembrar.siembra")} value={shortDate(start)} />
            <Box label={t("sembrar.cosecha")} value={shortDate(harvest!)} />
            <Box label={t("sembrar.dias")} value={String(cycle)} />
          </View>
          <Pressable accessibilityRole="button" onPress={() => onAdd(start)} style={styles.primary}>
            <Ionicons name="add" size={24} color={Colors.paper} />
            <Text style={styles.primaryText}>{t("sembrar.agregar")}</Text>
          </Pressable>
          <Pressable accessibilityRole="button" onPress={() => onPlan(harvest!)} style={styles.ghost}>
            <Ionicons name="refresh" size={24} color={Colors.fieldDeep} />
            <Text style={styles.ghostText}>{t("rotar.planificar")}</Text>
          </Pressable>
        </>
      )}
    </View>
  );
}

function Fact({ icon, label, value }: { icon: keyof typeof Ionicons.glyphMap; label: string; value: string }) {
  return (
    <View style={styles.fact}>
      <Ionicons name={icon} size={24} color={Colors.fieldDeep} />
      <View>
        <Text style={styles.small}>{label}</Text>
        <Text style={styles.factValue}>{value}</Text>
      </View>
    </View>
  );
}

function Box({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.box}>
      <Text style={styles.small}>{label}</Text>
      <Text style={styles.boxValue}>{value}</Text>
    </View>
  );
}

function Legend({ style, label }: { style: object; label: string }) {
  return (
    <View style={styles.legendRow}>
      <View style={[styles.swatch, style]} />
      <Text style={styles.small}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: Colors.paper },
  status: { paddingHorizontal: Spacing.gutter, paddingVertical: 4 },
  back: { flexDirection: "row", alignItems: "center", minHeight: 56, gap: 4 },
  backText: { ...Typography.label, color: Colors.ink },
  wall: { padding: Spacing.gutter, gap: 12, paddingBottom: 32 },
  title: { ...Typography.headline, color: Colors.ink },
  hero: { width: "100%", height: 200, borderRadius: Radius.card },
  facts: { flexDirection: "row", gap: 8 },
  fact: { flex: 1, flexDirection: "row", alignItems: "center", gap: 8, padding: 12, borderRadius: Radius.card, backgroundColor: Colors.paper2 },
  factValue: { ...Typography.label, color: Colors.ink },
  small: { ...Typography.meta, color: Colors.ink2 },
  two: { flexDirection: "row", gap: 8 },
  box: { flex: 1, padding: 12, borderRadius: Radius.card, borderWidth: 1, borderColor: Colors.line },
  boxValue: { ...Typography.title, color: Colors.ink },
  now: { gap: 6, padding: 16, borderRadius: Radius.sheet },
  nowHead: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 },
  nowTitle: { ...Typography.title, fontSize: 22, color: Colors.ink },
  verdict: { flexDirection: "row", alignItems: "center", gap: 4 },
  verdictText: { ...Typography.label },
  body: { ...Typography.body, fontSize: 18, color: Colors.ink2 },
  saved: { ...Typography.label, color: Colors.fieldDeep },
  primary: {
    minHeight: Touch.buttonHeight,
    borderRadius: Radius.btn,
    backgroundColor: Colors.field,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  primaryText: { ...Typography.label, fontSize: 19, color: Colors.paper },
  ghost: {
    minHeight: Touch.buttonHeight,
    borderRadius: Radius.btn,
    backgroundColor: Colors.fieldSoft,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  ghostText: { ...Typography.label, fontSize: 19, color: Colors.fieldDeep },
  source: { ...Typography.meta, color: Colors.ink2, textAlign: "center", paddingTop: 8 },
  monthHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  monthTitle: { ...Typography.title, color: Colors.ink },
  arrow: { width: 56, height: 56, alignItems: "center", justifyContent: "center" },
  grid: { flexDirection: "row", flexWrap: "wrap" },
  weekday: { width: `${100 / 7}%`, textAlign: "center", ...Typography.meta, color: Colors.ink2, paddingBottom: 4 },
  cell: { width: `${100 / 7}%`, aspectRatio: 1, padding: 2 },
  band: { backgroundColor: Colors.fieldSoft },
  day: { flex: 1, alignItems: "center", justifyContent: "center", borderRadius: 8 },
  good: { backgroundColor: "#D2E7D8" },
  bad: { backgroundColor: Colors.nowaterSoft },
  today: { borderWidth: 2, borderColor: Colors.ink },
  edge: { backgroundColor: Colors.field },
  dayText: { ...Typography.label, color: Colors.ink },
  pastText: { color: Colors.line },
  edgeText: { color: Colors.paper },
  legend: { flexDirection: "row", gap: 16, flexWrap: "wrap" },
  legendRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  swatch: { width: 18, height: 18, borderRadius: 4 },
  result: { gap: 4, padding: 14, borderRadius: Radius.card },
  resultTitle: { ...Typography.title },
});
