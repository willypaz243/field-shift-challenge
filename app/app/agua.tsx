import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { Colors, Radius, Spacing, Typography } from "../constants/Theme";
import { priorities, waterSources } from "../src/farm/types";
import { useFarm } from "../src/offline/provider";
import { LangToggle } from "../src/ui/LangToggle";
import { OptionGrid } from "../src/ui/OptionGrid";
import { PrimaryButton } from "../src/ui/PrimaryButton";
import { Steps } from "../src/ui/Steps";

export default function AguaScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { farm, saveFarm } = useFarm();
  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.status}>
        <Pressable accessibilityRole="button" onPress={() => router.back()} style={styles.back}>
          <Ionicons name="chevron-back" size={24} color={Colors.ink} />
          <Text style={styles.backText}>{t("comun.atras")}</Text>
        </Pressable>
        <LangToggle />
      </View>
      <ScrollView contentContainerStyle={styles.wall}>
        <Steps done={2} label={t("agua.paso")} />
        <Text style={styles.title}>{t("agua.titulo")}</Text>
        <View style={styles.sheet}>
          <Text style={styles.question}>{t("agua.pregunta_fuente")}</Text>
          <OptionGrid
            options={waterSources}
            selected={farm?.agua}
            label={(s) => t(`agua.fuente.${s}`)}
            onSelect={(agua) => void saveFarm({ agua })}
          />
        </View>
        <View style={styles.sheet}>
          <Text style={styles.question}>{t("agua.pregunta_prioridad")}</Text>
          <OptionGrid
            options={priorities}
            selected={farm?.prioridad}
            label={(p) => t(`agua.prioridad.${p}`)}
            onSelect={(prioridad) => void saveFarm({ prioridad })}
          />
        </View>
        <PrimaryButton label={t("comun.listo")} onPress={() => router.replace("/")} />
      </ScrollView>
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
  back: { flexDirection: "row", alignItems: "center", minHeight: 56, gap: 4 },
  backText: { ...Typography.label, color: Colors.ink },
  wall: { padding: Spacing.gutter, gap: 16, paddingBottom: 32 },
  title: { ...Typography.headline, color: Colors.ink },
  sheet: {
    gap: 10,
    padding: Spacing.cardPad,
    borderRadius: Radius.sheet,
    backgroundColor: Colors.paper2,
  },
  question: { ...Typography.title, fontSize: 22, color: Colors.ink },
});
