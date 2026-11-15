import { Pressable, StyleSheet, Text, View } from "react-native";
import { Colors, Radius, Typography } from "../../constants/Theme";

type Props<T extends string> = {
  options: readonly T[];
  selected?: T;
  label: (option: T) => string;
  onSelect: (option: T) => void;
};

export function OptionGrid<T extends string>({
  options,
  selected,
  label,
  onSelect,
}: Props<T>) {
  return (
    <View style={styles.grid}>
      {options.map((option) => {
        const on = option === selected;
        return (
          <Pressable
            key={option}
            accessibilityRole="button"
            accessibilityState={{ selected: on }}
            onPress={() => onSelect(option)}
            style={({ pressed }) => [
              styles.option,
              on && styles.on,
              pressed && styles.pressed,
            ]}
          >
            <Text style={[styles.text, on && styles.onText]}>
              {label(option)}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  option: {
    flexBasis: "48%",
    flexGrow: 1,
    minHeight: 64,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.line,
    backgroundColor: Colors.paper,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 8,
  },
  on: { backgroundColor: Colors.field, borderColor: Colors.field },
  pressed: { transform: [{ scale: 0.96 }] },
  text: {
    ...Typography.label,
    fontSize: 19,
    color: Colors.ink,
    textAlign: "center",
  },
  onText: { color: Colors.paper },
});
