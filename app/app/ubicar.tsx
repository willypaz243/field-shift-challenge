import { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { Colors, Radius, Spacing, Typography } from "../constants/Theme";
import { locatePhone } from "../src/farm/locate";
import { nearestZone } from "../src/farm/nearest";
import { zoneLabel, zones } from "../src/farm/zones";
import type { Point, Zone } from "../src/farm/types";
import { useFarm } from "../src/offline/provider";
import { LangToggle } from "../src/ui/LangToggle";
import { ZoneMap } from "../src/ui/ZoneMap";
import { PrimaryButton } from "../src/ui/PrimaryButton";
import { Steps } from "../src/ui/Steps";

type Place = { zone: Zone; point: Point };

const round3 = (n: number) => Math.round(n * 1000) / 1000;

export default function UbicarScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { saveFarm } = useFarm();
  const [place, setPlace] = useState<Place | null>(null);
  const [pin, setPin] = useState<Point | null>(null);
  const [choosing, setChoosing] = useState(false);
  const [locating, setLocating] = useState(true);

  useEffect(() => {
    void locatePhone().then((point) => {
      const zone = point && nearestZone(zones, point);
      if (point && zone) {
        setPlace({ zone, point });
        setPin(point);
      }
      else setChoosing(true);
      setLocating(false);
    });
  }, []);

  const confirm = async () => {
    if (!place) return;
    const plot = pin ?? place.point;
    await saveFarm({
      zone_id: place.zone.id,
      parcela: { lat: round3(plot.lat), lon: round3(plot.lon) },
    });
    router.push("/agua");
  };

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.status}>
        <Text style={styles.brand}>Choclito</Text>
        <LangToggle />
      </View>
      <View style={styles.wall}>
        <Steps done={1} label={t("ubicar.paso")} />
        {locating ? (
          <View style={styles.center}>
            <ActivityIndicator size="large" color={Colors.field} />
            <Text style={styles.body}>{t("ubicar.buscando")}</Text>
          </View>
        ) : choosing || !place ? (
          <>
            <Text style={styles.title}>{t("ubicar.elegir_zona")}</Text>
            <ScrollView contentContainerStyle={styles.list}>
              {zones.map((zone) => (
                <Pressable
                  key={zone.id}
                  accessibilityRole="button"
                  onPress={() => {
                    setPlace({ zone, point: zone });
                    setPin(zone);
                    setChoosing(false);
                  }}
                  style={({ pressed }) => [styles.row, pressed && styles.pressed]}
                >
                  <Text style={styles.rowText}>{zoneLabel(zone)}</Text>
                </Pressable>
              ))}
            </ScrollView>
          </>
        ) : (
          <>
            <Text style={styles.title}>{t("ubicar.titulo")}</Text>
            <ZoneMap
              zoneId={place.zone.id}
              center={place.point}
              pin={pin ?? place.point}
              onTap={setPin}
              credit={t("comun.mapa_gamc")}
              accessibilityLabel={t("ubicar.pista")}
            >
              <View style={styles.hint} pointerEvents="none">
                <Ionicons name="location" size={20} color={Colors.field} />
                <Text style={styles.hintText}>{t("ubicar.pista")}</Text>
              </View>
              <Text style={styles.zone} pointerEvents="none">
                {zoneLabel(place.zone)}
              </Text>
            </ZoneMap>
            <Pressable accessibilityRole="button" onPress={() => setChoosing(true)} style={styles.link}>
              <Text style={styles.linkText}>{t("ubicar.otra_zona")}</Text>
            </Pressable>
            <PrimaryButton label={t("ubicar.confirmar")} onPress={() => void confirm()} />
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: Colors.paper },
  status: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: Spacing.gutter,
    paddingVertical: 8,
  },
  brand: { ...Typography.title, fontSize: 22, color: Colors.fieldDeep },
  wall: { flex: 1, padding: Spacing.gutter, gap: 12 },
  title: { ...Typography.headline, color: Colors.ink },
  body: { ...Typography.body, color: Colors.ink2 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", gap: 12 },
  list: { gap: 8, paddingBottom: 16 },
  row: {
    minHeight: 64,
    justifyContent: "center",
    paddingHorizontal: 16,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.line,
  },
  rowText: { ...Typography.label, fontSize: 19, color: Colors.ink },
  pressed: { backgroundColor: Colors.paper2 },
  link: { minHeight: 56, justifyContent: "center", alignItems: "center" },
  hint: {
    position: "absolute",
    top: 10,
    left: 10,
    right: 10,
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    padding: 10,
    borderRadius: 12,
    backgroundColor: "rgba(255,255,255,0.95)",
  },
  hintText: { ...Typography.label, color: Colors.ink, flexShrink: 1 },
  zone: {
    position: "absolute",
    left: 10,
    bottom: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: "rgba(255,255,255,0.95)",
    ...Typography.meta,
    fontSize: 16,
    color: Colors.ink,
  },
  linkText: { ...Typography.label, color: Colors.fieldDeep, textDecorationLine: "underline" },
});
