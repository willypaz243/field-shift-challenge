import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import Svg, { Circle, G, Path, Rect } from "react-native-svg";
import { Ionicons } from "@expo/vector-icons";
import { Colors, Radius, Typography } from "../../constants/Theme";

// Illustrative plots: there are no plot polygons yet (API-CONTRACT §12), the
// farm is stored as the GPS point; the map only helps the farmer confirm it.
const PARCELS = [
  [10, 14, 120, 70],
  [140, 10, 80, 60],
  [234, 14, 96, 70],
  [14, 96, 90, 80],
  [140, 80, 80, 96],
  [230, 96, 102, 64],
  [8, 190, 104, 70],
  [122, 190, 100, 72],
  [240, 172, 92, 72],
  [16, 272, 100, 72],
  [128, 272, 92, 84],
  [232, 256, 100, 62],
  [10, 356, 104, 52],
  [248, 408, 84, 44],
  [236, 462, 96, 50],
  [140, 456, 86, 56],
] as const;
const START = 7;

export function ParcelMap({ hint, zone }: { hint: string; zone: string }) {
  const [selected, setSelected] = useState(START);
  const [x, y, w, h] = PARCELS[selected];
  return (
    <View style={styles.map}>
      <Svg
        viewBox="0 0 340 520"
        preserveAspectRatio="xMidYMid slice"
        style={StyleSheet.absoluteFill}
      >
        <Rect width={340} height={520} fill="#EEF3EC" />
        <Path
          d="M-10 500 C 70 470, 110 420, 180 400 S 290 372, 350 362"
          stroke={Colors.water}
          strokeWidth={6}
          fill="none"
          strokeLinecap="round"
        />
        {PARCELS.map(([px, py, pw, ph], i) => (
          <Rect
            key={i}
            x={px}
            y={py}
            width={pw}
            height={ph}
            rx={6}
            fill={i === selected ? Colors.field : Colors.paper}
            fillOpacity={i === selected ? 0.2 : 1}
            stroke={i === selected ? Colors.field : "#DCE6DB"}
            strokeWidth={i === selected ? 3 : 1.5}
            onPress={() => setSelected(i)}
          />
        ))}
        <G x={x + w / 2} y={y + h / 2}>
          <Circle r={26} fill={Colors.field} fillOpacity={0.16} />
          <Circle
            r={13}
            fill={Colors.field}
            stroke={Colors.paper}
            strokeWidth={4}
          />
        </G>
      </Svg>
      <View style={styles.hint} pointerEvents="none">
        <Ionicons name="location" size={20} color={Colors.field} />
        <Text style={styles.hintText}>{hint}</Text>
      </View>
      <Text style={styles.zone} pointerEvents="none">
        {zone}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  map: {
    flex: 1,
    minHeight: 300,
    borderRadius: Radius.card,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: Colors.line,
    backgroundColor: "#EEF3EC",
  },
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
});
