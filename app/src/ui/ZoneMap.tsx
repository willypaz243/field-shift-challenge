import { useState, type ReactNode } from "react";
import { Image, StyleSheet, Text, View } from "react-native";
import Svg, { Circle, Rect } from "react-native-svg";
import { Colors, Radius, Typography } from "../../constants/Theme";
import type { Point } from "../farm/types";
import { gamcMap } from "../zone/gamc";
import {
  clampCenter,
  floodMarks,
  imageRect,
  projectCells,
  projectPoint,
  unproject,
} from "../zone/map";

type Props = {
  zoneId: string;
  center: Point;
  pin?: Point;
  layers?: unknown;
  onTap?: (point: Point) => void;
  credit: string;
  children?: ReactNode;
  accessibilityLabel?: string;
};

// The GAMC layers are a georeferenced image; the plot, the reports and the
// taps use the same projection, so they land where they are on the ground.
export function ZoneMap({
  zoneId,
  center,
  pin,
  layers,
  onTap,
  credit,
  children,
  accessibilityLabel,
}: Props) {
  const [view, setView] = useState<{ width: number; height: number } | null>(
    null,
  );
  const base = gamcMap(zoneId);
  const origin = view && base ? clampCenter(center, view, base.bbox) : center;
  const rect = view && base ? imageRect(origin, view, base.bbox) : null;
  const cells = view ? projectCells(layers, origin, view) : [];
  const floods = view ? floodMarks(layers, origin, view) : [];
  const dot = view && pin ? projectPoint(origin, view, pin) : null;

  return (
    <View
      style={styles.map}
      accessibilityLabel={accessibilityLabel}
      onLayout={(e) =>
        setView({
          width: e.nativeEvent.layout.width,
          height: e.nativeEvent.layout.height,
        })
      }
    >
      {rect && base && (
        <Image
          source={base.image}
          resizeMode="stretch"
          style={{
            position: "absolute",
            left: rect.left,
            top: rect.top,
            width: rect.width,
            height: rect.height,
          }}
        />
      )}
      {view && (
        <View
          style={StyleSheet.absoluteFill}
          onStartShouldSetResponder={() => !!onTap}
          // Responder events carry the tap position on native and on web;
          // Pressable's onPress does not on web.
          onResponderRelease={(e) => {
            const { locationX: x, locationY: y } = e.nativeEvent;
            if (Number.isFinite(x) && Number.isFinite(y))
              onTap?.(unproject(origin, view, x, y));
          }}
        >
          <Svg width={view.width} height={view.height} pointerEvents="none">
            {cells.map((c, i) => (
              <Rect
                key={i}
                x={c.x}
                y={c.y}
                width={c.w}
                height={c.h}
                rx={6}
                fill={Colors.nowater}
                fillOpacity={0.18}
                stroke={Colors.nowater}
                strokeWidth={2}
              />
            ))}
            {floods.map((f, i) => (
              <Circle
                key={i}
                cx={f.cx}
                cy={f.cy}
                r={28}
                fill={Colors.water}
                fillOpacity={0.18}
                stroke={Colors.water}
                strokeWidth={2}
              />
            ))}
            {dot && (
              <>
                <Circle
                  cx={dot.x}
                  cy={dot.y}
                  r={26}
                  fill={Colors.field}
                  fillOpacity={0.18}
                />
                <Circle
                  cx={dot.x}
                  cy={dot.y}
                  r={13}
                  fill={Colors.field}
                  stroke={Colors.paper}
                  strokeWidth={4}
                />
              </>
            )}
          </Svg>
        </View>
      )}
      {children}
      <Text style={styles.credit} pointerEvents="none">
        {credit}
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
    backgroundColor: "#F4F2EC",
  },
  credit: {
    position: "absolute",
    right: 6,
    bottom: 4,
    ...Typography.meta,
    fontSize: 12,
    color: Colors.ink2,
    backgroundColor: "rgba(255,255,255,0.8)",
    paddingHorizontal: 4,
    borderRadius: 4,
    overflow: "hidden",
  },
});
