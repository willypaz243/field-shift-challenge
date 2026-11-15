import { useMemo, useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTranslation } from "react-i18next";
import { Colors, Radius, Spacing, Touch, Typography } from "../constants/Theme";
import { sourceLine } from "../src/calendar/calendar";
import { MyCrops } from "../src/farm/my-crops";
import { priorities, type Priority } from "../src/farm/types";
import { cropName, notifyMyCrops } from "../src/mycrops/use-my-crops";
import { useFarm, useOffline } from "../src/offline/provider";
import { defaultGoal, planDates, planFor, rankFor, rotationsFor, season, type RankedRotation } from "../src/rotations/rotations";
import { cycleDays, findCrop } from "../src/sow/sow";
import { cropImages } from "../src/ui/crop-images";
import { laPazToday, monthName, shortDate } from "../src/ui/dates";
import { Sheet } from "../src/ui/Sheet";

type Icon = keyof typeof Ionicons.glyphMap;
const GOAL_ICON: Record<Priority, Icon> = { agua: "water-outline", tierra: "leaf-outline", forraje: "nutrition-outline", vender: "storefront-outline" };
const DEFAULT_EMPTY_MONTHS = 6;

const humanize = (code: string) => code.charAt(0).toUpperCase() + code.slice(1).replace(/_/g, " ");

export default function RotarScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { c, h } = useLocalSearchParams<{ c: string; h?: string }>();
  const { client, zone, data } = useOffline();
  const { farm, saveFarm } = useFarm();
  const harvest = h ?? laPazToday();
  const plans = useMemo(() => rotationsFor(data?.rotaciones, c), [data, c]);
  const nextSowing = planDates(harvest, 0).siembra;
  const [goal, setGoal] = useState<Priority>(defaultGoal(farm?.prioridad, nextSowing));
  const [open, setOpen] = useState<RankedRotation | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const ranked = rankFor(plans, goal);
  const code = (k: string) => t(`rotar.codigo.${k}`, { defaultValue: humanize(k) });
  const nameA = cropName(data, c);
  const title = (r: RankedRotation) =>
    r.secuencia[1]
      ? t("rotar.luego", { a: nameA, b: cropName(data, r.secuencia[1]).toLowerCase() })
      : t("rotar.solo", { a: nameA.toLowerCase() });
  const datesOf = (r: RankedRotation) => {
    const next = r.secuencia[1] ? findCrop(data, r.secuencia[1]) : null;
    return next ? planDates(harvest, cycleDays(next)) : null;
  };
  const emptyUntil = (r: RankedRotation) => {
    const months = r.meses_sin_cultivo ?? DEFAULT_EMPTY_MONTHS;
    const m = ((Number(harvest.slice(5, 7)) - 1 + months) % 12) + 1;
    return monthName(m).slice(0, 3);
  };

  const choose = async (r: RankedRotation) => {
    const next = r.secuencia[1];
    const dates = datesOf(r);
    if (!next || !dates) return;
    await new MyCrops(client.store.db).add({ crop_id: next, ...dates, planificado: true });
    await client.outbox.enqueue(planFor(r, zone, dates.siembra));
    void client.outbox.flush().catch(() => undefined);
    notifyMyCrops();
    setOpen(null);
    setSaved(t("rotar.guardado", { b: cropName(data, next).toLowerCase(), fecha: shortDate(dates.siembra) }));
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
        <Text style={styles.title}>{t("rotar.titulo")}</Text>
        <View style={styles.goal}>
          <Text style={styles.question}>{t("rotar.que_buscas")}</Text>
          <View style={styles.goals}>
            {priorities.map((g) => {
              const on = g === goal;
              return (
                <Pressable
                  key={g}
                  accessibilityRole="radio"
                  accessibilityState={{ selected: on }}
                  onPress={() => {
                    setGoal(g);
                    void saveFarm({ prioridad: g });
                  }}
                  style={[styles.goalBtn, on && styles.goalOn]}
                >
                  <Ionicons name={GOAL_ICON[g]} size={22} color={on ? Colors.paper : Colors.fieldDeep} />
                  <Text style={[styles.goalText, on && { color: Colors.paper }]}>{t(`rotar.objetivo.${g}`)}</Text>
                </Pressable>
              );
            })}
          </View>
          <Text style={styles.why}>
            {t(`rotar.razon.${season(nextSowing)}_${goal}`, { mes: monthName(Number(nextSowing.slice(5, 7))) })}
          </Text>
        </View>
        {saved && <Text style={styles.saved}>{saved}</Text>}
        {ranked.length === 0 && <Text style={styles.why}>{t("rotar.sin_datos")}</Text>}
        {ranked.map((r) => {
          const dates = datesOf(r);
          const b = r.secuencia[1];
          return (
            <Pressable
              key={r.id}
              accessibilityRole="button"
              onPress={() => setOpen(r)}
              style={({ pressed }) => [styles.plan, r.mejor && styles.best, pressed && styles.pressed]}
            >
              <View style={styles.pics}>
                <Pic id={c} />
                <Ionicons name="chevron-forward" size={22} color={Colors.ink2} />
                {b ? <Pic id={b} /> : <View style={[styles.pic, styles.none]}><Text style={styles.small}>{t("rotar.nada")}</Text></View>}
              </View>
              <View style={styles.dates}>
                <Text style={styles.small}>
                  {t("rotar.cosecha")} <Text style={styles.dateValue}>{shortDate(harvest)}</Text>
                </Text>
                <Text style={styles.small}>
                  {dates ? t("rotar.siembra") : t("rotar.vacio_hasta")}{" "}
                  <Text style={styles.dateValue}>
                    {dates ? `${shortDate(dates.siembra)} → ${monthName(Number(dates.cosecha.slice(5, 7))).slice(0, 3)}` : emptyUntil(r)}
                  </Text>
                </Text>
              </View>
              <Text style={styles.planTitle}>{title(r)}</Text>
              {(r.mejor || r.actual) && (
                <Text style={[styles.tag, r.mejor && styles.bestTag]}>{r.mejor ? t("rotar.mejor") : t("rotar.actual")}</Text>
              )}
              <View style={styles.chips}>
                {(r.etiquetas ?? []).slice(0, 3).map(([k, tone]) => (
                  <Text key={k} style={[styles.chip, tone === "bien" && styles.good, tone === "mal" && styles.bad]}>
                    {code(k)}
                  </Text>
                ))}
              </View>
            </Pressable>
          );
        })}
      </ScrollView>
      <Sheet visible={open !== null} title={open ? title(open) : ""} subtitle={open?.confianza ? t(`rotar.confianza.${open.confianza}`) : undefined} closeLabel={t("comun.cerrar")} onClose={() => setOpen(null)}>
        {open?.por_que && <Block label={t("rotar.por_que")} items={[code(open.por_que)]} />}
        {!!open?.bueno?.length && <Block label={t("rotar.bueno")} items={open.bueno.map(code)} />}
        {!!open?.riesgos?.length && <Block label={t("rotar.riesgos")} items={open.riesgos.map(code)} />}
        {!!open?.falta_saber?.length && <Block label={t("rotar.falta")} items={open.falta_saber.map(code)} />}
        {!!open?.evidencia?.length && (
          <Block label={t("rotar.datos")} items={open.evidencia.map((e) => `${code(e.codigo)}${e.fuente ? ` · ${sourceLine([e.fuente])}` : ""}`)} />
        )}
        {open?.secuencia[1] && (
          <Pressable accessibilityRole="button" onPress={() => void choose(open)} style={styles.primary}>
            <Ionicons name="checkmark" size={24} color={Colors.paper} />
            <Text style={styles.primaryText}>{t("rotar.quiero")}</Text>
          </Pressable>
        )}
      </Sheet>
    </SafeAreaView>
  );
}

function Pic({ id }: { id: string }) {
  return cropImages[id] ? <Image source={cropImages[id]} style={styles.pic} /> : <View style={[styles.pic, styles.none]} />;
}

function Block({ label, items }: { label: string; items: string[] }) {
  return (
    <View style={{ gap: 4, paddingBottom: 8 }}>
      <Text style={styles.blockLabel}>{label}</Text>
      {items.map((item) => (
        <Text key={item} style={styles.blockItem}>
          {`• ${item}`}
        </Text>
      ))}
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
  goal: { gap: 10, padding: 16, borderRadius: Radius.sheet, backgroundColor: Colors.paper2 },
  question: { ...Typography.title, fontSize: 22, color: Colors.ink },
  goals: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  goalBtn: {
    flexBasis: "48%",
    flexGrow: 1,
    minHeight: 56,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.line,
    backgroundColor: Colors.paper,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
  },
  goalOn: { backgroundColor: Colors.field, borderColor: Colors.field },
  goalText: { ...Typography.label, color: Colors.ink },
  why: { ...Typography.body, fontSize: 17, color: Colors.ink2 },
  saved: { ...Typography.label, color: Colors.fieldDeep },
  plan: { gap: 8, padding: 14, borderRadius: Radius.card, borderWidth: 1, borderColor: Colors.line },
  best: { borderColor: Colors.field, borderWidth: 2 },
  pressed: { backgroundColor: Colors.paper2 },
  pics: { flexDirection: "row", alignItems: "center", gap: 8 },
  pic: { width: 72, height: 56, borderRadius: 10 },
  none: { backgroundColor: Colors.paper2, alignItems: "center", justifyContent: "center" },
  dates: { flexDirection: "row", justifyContent: "space-between", flexWrap: "wrap", gap: 8 },
  small: { ...Typography.meta, color: Colors.ink2 },
  dateValue: { ...Typography.label, color: Colors.ink },
  planTitle: { ...Typography.title, color: Colors.ink },
  tag: {
    alignSelf: "flex-start",
    ...Typography.meta,
    color: Colors.paper,
    backgroundColor: Colors.ink,
    borderRadius: Radius.pill,
    overflow: "hidden",
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  bestTag: { backgroundColor: Colors.field },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  chip: {
    ...Typography.meta,
    color: Colors.ink2,
    backgroundColor: Colors.paper2,
    borderRadius: Radius.pill,
    overflow: "hidden",
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  good: { color: Colors.fieldDeep, backgroundColor: Colors.fieldSoft },
  bad: { color: Colors.dry, backgroundColor: Colors.drySoft },
  blockLabel: { ...Typography.label, color: Colors.ink },
  blockItem: { ...Typography.body, fontSize: 17, color: Colors.ink2 },
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
});
