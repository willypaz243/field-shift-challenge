import { useRef, useState, type ReactNode } from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import Svg, { Circle, Rect } from "react-native-svg";
import { Colors, Radius, Typography } from "../../constants/Theme";
import type { Point } from "../farm/types";
import { gamcMap } from "../zone/gamc";
import {
  clampCenter,
  clampZoom,
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
  zoomLabels?: { in: string; out: string };
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
  zoomLabels,
}: Props) {
  const [size, setSize] = useState<{ width: number; height: number } | null>(
    null,
  );
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState<Point | null>(null);
  const gesture = useRef<{
    x: number;
    y: number;
    distance: number;
    zoom: number;
    origin: Point;
    moved: boolean;
  } | null>(null);
  const base = gamcMap(zoneId);
  const view = size && { ...size, zoom };
  const origin =
    view && base
      ? clampCenter(pan ?? center, view, base.bbox)
      : (pan ?? center);
  const rect = view && base ? imageRect(origin, view, base.bbox) : null;
  const cells = view ? projectCells(layers, origin, view) : [];
  const floods = view ? floodMarks(layers, origin, view) : [];
  const dot = view && pin ? projectPoint(origin, view, pin) : null;

  const distance = (touches: { pageX: number; pageY: number }[]) =>
    touches.length > 1
      ? Math.hypot(
          touches[0].pageX - touches[1].pageX,
          touches[0].pageY - touches[1].pageY,
        )
      : 0;

  const changeZoom = (next: number) => setZoom(clampZoom(next));

  return (
    <View
      style={styles.map}
      accessibilityLabel={accessibilityLabel}
      onLayout={(e) =>
        setSize({
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
          // Responder events carry the touch position on native and on web;
          // Pressable's onPress does not on web. The map keeps the gesture so
          // a surrounding scroll view does not steal the drag.
          onStartShouldSetResponder={() => true}
          onResponderTerminationRequest={() => false}
          onResponderGrant={(e) => {
            const n = e.nativeEvent;
            gesture.current = {
              x: n.locationX,
              y: n.locationY,
              distance: distance(n.touches as never),
              zoom,
              origin,
              moved: false,
            };
          }}
          onResponderMove={(e) => {
            const g = gesture.current;
            if (!g) return;
            const n = e.nativeEvent;
            const d = distance(n.touches as never);
            if (d > 0 && g.distance > 0) {
              g.moved = true;
              changeZoom(g.zoom * (d / g.distance));
              return;
            }
            const dx = n.locationX - g.x;
            const dy = n.locationY - g.y;
            if (Math.hypot(dx, dy) > 8) g.moved = true;
            if (g.moved && Number.isFinite(dx) && Number.isFinite(dy))
              setPan(
                unproject(
                  g.origin,
                  { ...view, zoom: g.zoom },
                  view.width / 2 - dx,
                  view.height / 2 - dy,
                ),
              );
          }}
          onResponderRelease={(e) => {
            const g = gesture.current;
            gesture.current = null;
            if (!g || g.moved) return;
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
      <View style={styles.zoom}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={zoomLabels?.in}
          onPress={() => changeZoom(zoom + 0.5)}
          style={styles.zoomButton}
        >
          <Ionicons name="add" size={28} color={Colors.ink} />
        </Pressable>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={zoomLabels?.out}
          onPress={() => changeZoom(zoom - 0.5)}
          style={[styles.zoomButton, styles.zoomDivider]}
        >
          <Ionicons name="remove" size={28} color={Colors.ink} />
        </Pressable>
      </View>
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
  zoom: {
    position: "absolute",
    right: 10,
    top: 10,
    borderRadius: Radius.btn,
    backgroundColor: "rgba(255,255,255,0.95)",
    borderWidth: 1,
    borderColor: Colors.line,
  },
  zoomButton: {
    width: 56,
    height: 56,
    alignItems: "center",
    justifyContent: "center",
  },
  zoomDivider: { borderTopWidth: 1, borderTopColor: Colors.line },
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
