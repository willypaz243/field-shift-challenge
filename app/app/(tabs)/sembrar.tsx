import { useMemo, useRef, useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import {
  FlatList,
  Image,
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from "react-native";
import { useTranslation } from "react-i18next";
import { Colors, Radius, Spacing, Typography } from "../../constants/Theme";
import { useOffline } from "../../src/offline/provider";
import type { Crop } from "../../src/scoring/scoring";
import { bestNow, cycleDays } from "../../src/sow/sow";
import { cropImages } from "../../src/ui/crop-images";
import { laPazToday } from "../../src/ui/dates";

type CatalogCrop = Crop & { nombre: string };

export default function SembrarScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { data } = useOffline();
  const { width } = useWindowDimensions();
  const cardWidth = width - Spacing.gutter * 4;
  const list = useRef<FlatList<CatalogCrop & { best: boolean }>>(null);
  const [index, setIndex] = useState(0);
  const today = laPazToday();

  const crops = useMemo(() => {
    const catalog = ((data?.crops as { crops?: CatalogCrop[] } | undefined)?.crops ?? []).map((c) => ({
      ...c,
      best: bestNow(data, c.id, today),
    }));
    return [...catalog.filter((c) => c.best), ...catalog.filter((c) => !c.best)];
  }, [data, today]);

  const onViewable = useRef(({ viewableItems }: { viewableItems: { index?: number | null }[] }) => {
    if (viewableItems[0]?.index != null) setIndex(viewableItems[0].index);
  }).current;
  const go = (step: number) => {
    const next = Math.max(0, Math.min(crops.length - 1, index + step));
    list.current?.scrollToIndex({ index: next, animated: true });
  };

  return (
    <View style={styles.screen}>
      <Text style={styles.title}>{t("sembrar.titulo")}</Text>
      <FlatList
        ref={list}
        data={crops}
        horizontal
        keyExtractor={(c) => c.id}
        showsHorizontalScrollIndicator={false}
        snapToInterval={cardWidth + 12}
        decelerationRate="fast"
        contentContainerStyle={{ paddingHorizontal: Spacing.gutter * 2, gap: 12 }}
        onViewableItemsChanged={onViewable}
        viewabilityConfig={{ itemVisiblePercentThreshold: 60 }}
        getItemLayout={(_, i) => ({ length: cardWidth + 12, offset: (cardWidth + 12) * i, index: i })}
        renderItem={({ item }) => (
          <Pressable
            accessibilityRole="button"
            onPress={() => router.push({ pathname: "/cultivo/[id]", params: { id: item.id } })}
            style={({ pressed }) => [styles.card, { width: cardWidth }, item.best && styles.best, pressed && styles.pressed]}
          >
            {cropImages[item.id] && <Image source={cropImages[item.id]} style={styles.photo} resizeMode="cover" />}
            {item.best && (
              <View style={styles.badge}>
                <Ionicons name="checkmark" size={18} color={Colors.paper} />
                <Text style={styles.badgeText}>{t("sembrar.mejor_epoca")}</Text>
              </View>
            )}
            <View style={styles.text}>
              <Text style={styles.name}>{item.nombre}</Text>
              <Text style={styles.body}>{t("sembrar.ciclo", { dias: cycleDays(item) })}</Text>
              <View style={styles.go}>
                <Text style={styles.goText}>{t("sembrar.ver_cuando")}</Text>
                <Ionicons name="chevron-forward" size={20} color={Colors.fieldDeep} />
              </View>
            </View>
          </Pressable>
        )}
      />
      <View style={styles.controls}>
        <Pressable accessibilityRole="button" accessibilityLabel={t("sembrar.anterior")} onPress={() => go(-1)} style={styles.arrow}>
          <Ionicons name="chevron-back" size={26} color={Colors.ink} />
        </Pressable>
        <View style={styles.dots}>
          {crops.map((c, i) => (
            <View key={c.id} style={[styles.dot, i === index && styles.dotOn]} />
          ))}
        </View>
        <Pressable accessibilityRole="button" accessibilityLabel={t("sembrar.siguiente")} onPress={() => go(1)} style={styles.arrow}>
          <Ionicons name="chevron-forward" size={26} color={Colors.ink} />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: Colors.paper, paddingVertical: Spacing.gutter, gap: 12 },
  title: { ...Typography.headline, color: Colors.ink, paddingHorizontal: Spacing.gutter },
  card: {
    flex: 1,
    borderRadius: Radius.sheet,
    borderWidth: 1,
    borderColor: Colors.line,
    backgroundColor: Colors.paper,
    overflow: "hidden",
  },
  best: { borderColor: Colors.field, borderWidth: 2 },
  pressed: { transform: [{ scale: 0.98 }] },
  photo: { width: "100%", flex: 1, minHeight: 200 },
  badge: {
    position: "absolute",
    top: 12,
    left: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: Radius.pill,
    backgroundColor: Colors.field,
  },
  badgeText: { ...Typography.meta, color: Colors.paper },
  text: { padding: 16, gap: 6 },
  name: { ...Typography.headline, color: Colors.ink },
  body: { ...Typography.body, color: Colors.ink2 },
  go: { flexDirection: "row", alignItems: "center", gap: 4, minHeight: 44 },
  goText: { ...Typography.label, color: Colors.fieldDeep },
  controls: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: Spacing.gutter },
  arrow: { width: 56, height: 56, borderRadius: 28, backgroundColor: Colors.paper2, alignItems: "center", justifyContent: "center" },
  dots: { flexDirection: "row", gap: 6, flexWrap: "wrap", justifyContent: "center", flex: 1 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: Colors.line },
  dotOn: { backgroundColor: Colors.field, width: 20 },
});
