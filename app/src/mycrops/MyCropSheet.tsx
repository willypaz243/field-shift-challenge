import { useState } from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";
import { Colors, Radius, Typography } from "../../constants/Theme";
import { sourceLine } from "../calendar/calendar";
import {
  Harvests,
  feedbackFor,
  monthTimeline,
  type Resultado,
} from "./mycrops";
import { cropName, notifyMyCrops } from "./use-my-crops";
import type { MyCrop } from "../farm/my-crops";
import { useOffline } from "../offline/provider";
import { cropImages } from "../ui/crop-images";
import { laPazToday, monthName, shortDate } from "../ui/dates";
import { Sheet } from "../ui/Sheet";

const RESULTS: { id: Resultado; color: string }[] = [
  { id: "buena", color: Colors.field },
  { id: "regular", color: "#D99A1E" },
  { id: "mala", color: Colors.nowater },
];

export function useAnswerHarvest() {
  const { client, zone } = useOffline();
  return async (crop: MyCrop, resultado: Resultado) => {
    await client.outbox.enqueue(feedbackFor(crop, zone, resultado));
    await new Harvests(client.store.db).answer(crop.id, resultado);
    void client.outbox.flush().catch(() => undefined);
    notifyMyCrops();
  };
}

export function ResultButtons({ onPick }: { onPick: (r: Resultado) => void }) {
  const { t } = useTranslation();
  return (
    <View style={styles.results}>
      {RESULTS.map((r) => (
        <Pressable
          key={r.id}
          accessibilityRole="button"
          onPress={() => onPick(r.id)}
          style={styles.result}
        >
          <View style={[styles.dot, { backgroundColor: r.color }]} />
          <Text style={styles.resultText}>
            {t(`cultivos.resultado.${r.id}`)}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

export function MyCropSheet({
  crop,
  onClose,
}: {
  crop: MyCrop | null;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const { data } = useOffline();
  const answer = useAnswerHarvest();
  const [rating, setRating] = useState(false);
  const [done, setDone] = useState(false);
  const today = laPazToday();
  if (!crop) return null;
  const catalog = (
    data?.crops as
      { crops?: { id: string; etapas?: [number, string][] }[] } | undefined
  )?.crops;
  const etapas = catalog?.find((c) => c.id === crop.crop_id)?.etapas ?? [];
  const clima = data?.climatologia as
    { fuente?: string[]; periodo?: { power?: string } } | undefined;
  const months = monthTimeline(crop, etapas, data?.climatologia);
  const close = () => {
    setRating(false);
    setDone(false);
    onClose();
  };
  return (
    <Sheet
      visible
      title={cropName(data, crop.crop_id)}
      closeLabel={t("comun.cerrar")}
      onClose={close}
    >
      {cropImages[crop.crop_id] && (
        <Image
          source={cropImages[crop.crop_id]}
          style={styles.hero}
          resizeMode="cover"
        />
      )}
      <View style={styles.two}>
        <View style={styles.box}>
          <Text style={styles.small}>
            {crop.planificado ? t("cultivos.siembra") : t("cultivos.sembraste")}
          </Text>
          <Text style={styles.boxValue}>{shortDate(crop.siembra)}</Text>
        </View>
        <View style={styles.box}>
          <Text style={styles.small}>{t("cultivos.cosecha")}</Text>
          <Text style={styles.boxValue}>{shortDate(crop.cosecha)}</Text>
        </View>
      </View>
      <Text style={styles.section}>{t("cultivos.calendario")}</Text>
      {months.map((m) => {
        const isNow =
          `${m.anio}-${String(m.mes).padStart(2, "0")}` === today.slice(0, 7);
        return (
          <View
            key={`${m.anio}-${m.mes}`}
            style={[styles.month, isNow && styles.now]}
          >
            <Text style={styles.monthName}>{monthName(m.mes).slice(0, 3)}</Text>
            <View style={{ flex: 1, gap: 4 }}>
              {isNow && (
                <Text style={styles.nowTag}>{t("cultivos.ahora")}</Text>
              )}
              <Text style={styles.stage}>
                {t(`cultivos.etapa.${m.etapa}`, { defaultValue: m.etapa })}
              </Text>
              {m.helada && (
                <Text style={styles.frost}>{t("cultivos.heladas")}</Text>
              )}
            </View>
          </View>
        );
      })}
      <Text style={styles.source}>
        {t("cultivos.fuente_riesgos", {
          fuentes: sourceLine(clima?.fuente),
          periodo: clima?.periodo?.power ?? "",
        })}
      </Text>
      {!crop.planificado && !done && !rating && (
        <Pressable
          accessibilityRole="button"
          onPress={() => setRating(true)}
          style={styles.ghost}
        >
          <Text style={styles.ghostText}>{t("cultivos.ya_coseche")}</Text>
        </Pressable>
      )}
      {rating && !done && (
        <>
          <Text style={styles.section}>{t("cultivos.como_salio")}</Text>
          <ResultButtons
            onPick={(r) => {
              void answer(crop, r);
              setDone(true);
            }}
          />
        </>
      )}
      {done && <Text style={styles.thanks}>{t("cultivos.gracias")}</Text>}
    </Sheet>
  );
}

const styles = StyleSheet.create({
  hero: { width: "100%", height: 180, borderRadius: Radius.card },
  two: { flexDirection: "row", gap: 8 },
  box: {
    flex: 1,
    padding: 12,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.line,
  },
  small: { ...Typography.meta, color: Colors.ink2 },
  boxValue: { ...Typography.title, color: Colors.ink },
  section: {
    ...Typography.title,
    fontSize: 22,
    color: Colors.ink,
    paddingTop: 8,
  },
  month: {
    flexDirection: "row",
    gap: 12,
    alignItems: "flex-start",
    padding: 10,
    borderRadius: 12,
  },
  now: { backgroundColor: Colors.fieldSoft },
  monthName: {
    ...Typography.label,
    width: 44,
    color: Colors.ink2,
    textTransform: "capitalize",
  },
  nowTag: { ...Typography.meta, color: Colors.fieldDeep },
  stage: { ...Typography.label, fontSize: 19, color: Colors.ink },
  frost: { ...Typography.meta, color: Colors.frost },
  source: { ...Typography.meta, color: Colors.ink2, paddingTop: 8 },
  ghost: {
    minHeight: 60,
    borderRadius: Radius.btn,
    backgroundColor: Colors.fieldSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  ghostText: { ...Typography.label, fontSize: 19, color: Colors.fieldDeep },
  results: { flexDirection: "row", gap: 8 },
  result: {
    flex: 1,
    minHeight: 64,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.line,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  dot: { width: 14, height: 14, borderRadius: 7 },
  resultText: { ...Typography.label, fontSize: 19, color: Colors.ink },
  thanks: { ...Typography.label, color: Colors.fieldDeep },
});
