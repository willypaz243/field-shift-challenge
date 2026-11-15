import { StyleSheet, Text, View } from "react-native";
import { Colors, Typography } from "../../constants/Theme";

export function Steps({ done, label }: { done: number; label: string }) {
  return (
    <View style={styles.row}>
      {[0, 1].map((i) => (
        <View key={i} style={[styles.bar, i < done && styles.on]} />
      ))}
      <Text style={styles.text}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: 6 },
  bar: { width: 40, height: 6, borderRadius: 3, backgroundColor: Colors.line },
  on: { backgroundColor: Colors.field },
  text: { ...Typography.meta, color: Colors.ink2 },
});
