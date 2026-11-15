import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";
import { Colors } from "../../constants/Theme";
import { newCount } from "../alerts/alerts";
import { useSeenAlerts } from "../alerts/use-seen";
import { useOffline } from "../offline/provider";

export function Bell() {
  const { t } = useTranslation();
  const router = useRouter();
  const { data } = useOffline();
  const { seen } = useSeenAlerts();
  const count = newCount(data?.alertas, seen);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={t("avisos.campana", { count })}
      onPress={() => router.push("/avisos")}
      style={styles.bell}
    >
      <Ionicons name="notifications-outline" size={26} color={Colors.ink} />
      {count > 0 && (
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{count}</Text>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  bell: {
    minWidth: 56,
    minHeight: 56,
    justifyContent: "center",
    alignItems: "center",
  },
  badge: {
    position: "absolute",
    top: 8,
    right: 8,
    minWidth: 20,
    height: 20,
    paddingHorizontal: 4,
    borderRadius: 10,
    backgroundColor: Colors.nowater,
    justifyContent: "center",
    alignItems: "center",
  },
  badgeText: {
    color: Colors.paper,
    fontSize: 12,
    fontFamily: "AtkinsonHyperlegibleNext-Bold",
  },
});
