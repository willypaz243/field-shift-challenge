import * as Location from "expo-location";
import type { Point } from "./types";

const GPS_TIMEOUT_MS = 10_000;

// Resolves null when the farmer says no or the phone cannot find itself in time,
// so the screen falls back to the zone list instead of waiting.
export async function locatePhone(): Promise<Point | null> {
  try {
    const { granted } = await Location.requestForegroundPermissionsAsync();
    if (!granted) return null;
    const timeout = new Promise<null>((resolve) =>
      setTimeout(() => resolve(null), GPS_TIMEOUT_MS),
    );
    const position = await Promise.race([
      Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      }),
      timeout,
    ]);
    return (
      position && {
        lat: position.coords.latitude,
        lon: position.coords.longitude,
      }
    );
  } catch {
    return null;
  }
}
