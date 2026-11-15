import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text } from "react-native";
import { Colors, Radius, Touch, Typography } from "../../constants/Theme";

export function PrimaryButton({
  label,
  onPress,
}: {
  label: string;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.button, pressed && styles.pressed]}
    >
      <Ionicons name="checkmark" size={24} color={Colors.paper} />
      <Text style={styles.text}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: Touch.buttonHeight,
    borderRadius: Radius.btn,
    backgroundColor: Colors.field,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  pressed: { transform: [{ scale: 0.97 }], backgroundColor: Colors.fieldDeep },
  text: { ...Typography.label, fontSize: 19, color: Colors.paper },
});
