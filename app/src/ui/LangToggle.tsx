import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTranslation } from "react-i18next";
import { Colors, Typography } from "../../constants/Theme";
import { useFarm } from "../offline/provider";
import type { Language } from "../farm/types";

const LANGUAGES: Language[] = ["es", "qu"];

export function LangToggle({ compact = false }: { compact?: boolean }) {
  const { i18n } = useTranslation();
  const { saveFarm } = useFarm();
  if (compact) {
    // The tab header has room for one button: it shows the current language
    // and switches to the other one.
    const next = i18n.language === "qu" ? "es" : "qu";
    return (
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={next.toUpperCase()}
        onPress={() => void saveFarm({ idioma: next })}
        style={[styles.button, styles.on, styles.single]}
      >
        <Text style={[styles.text, styles.onText]}>
          {i18n.language === "qu" ? "QU" : "ES"}
        </Text>
      </Pressable>
    );
  }
  return (
    <View style={styles.group} accessibilityRole="radiogroup">
      {LANGUAGES.map((language) => {
        const on = i18n.language === language;
        return (
          <Pressable
            key={language}
            accessibilityRole="radio"
            accessibilityState={{ selected: on }}
            onPress={() => void saveFarm({ idioma: language })}
            style={[styles.button, on && styles.on]}
          >
            <Text style={[styles.text, on && styles.onText]}>
              {language.toUpperCase()}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  group: {
    flexDirection: "row",
    borderRadius: 999,
    borderWidth: 1,
    borderColor: Colors.line,
    overflow: "hidden",
  },
  button: {
    minWidth: 56,
    minHeight: 56,
    alignItems: "center",
    justifyContent: "center",
  },
  on: { backgroundColor: Colors.fieldDeep },
  single: { borderRadius: 28 },
  text: { ...Typography.label, color: Colors.ink2 },
  onText: { color: Colors.paper },
});
