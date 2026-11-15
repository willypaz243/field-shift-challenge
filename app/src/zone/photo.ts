import { Directory, File, Paths } from "expo-file-system";
import { ImageManipulator, SaveFormat } from "expo-image-manipulator";
import * as ImagePicker from "expo-image-picker";
import type { SQLiteDatabase } from "expo-sqlite";
import { orphanPhotos, shrinkWith } from "./photo-size";

export type Photo = { uri: string; name: string; type: string };

// The picker's copy lives in the cache, which the system may clear before the
// report is sent; queued photos are kept in the documents folder instead.
function photosDir() {
  const dir = new Directory(Paths.document, "reports");
  if (!dir.exists) dir.create({ intermediates: true });
  return dir;
}

// null when the farmer cancels; "too_big" when no size step fits the limit.
export async function takePhoto(): Promise<Photo | null | "too_big"> {
  const camera = await ImagePicker.requestCameraPermissionsAsync();
  const options: ImagePicker.ImagePickerOptions = {
    mediaTypes: ["images"],
    quality: 0.8,
  };
  const picked = camera.granted
    ? await ImagePicker.launchCameraAsync(options)
    : await ImagePicker.launchImageLibraryAsync(options);
  if (picked.canceled || !picked.assets[0]) return null;
  const source = picked.assets[0].uri;
  const small = await shrinkWith(async (width, compress) => {
    const context = ImageManipulator.manipulate(source);
    context.resize({ width });
    const image = await context.renderAsync();
    const saved = await image.saveAsync({ compress, format: SaveFormat.JPEG });
    return { uri: saved.uri, size: new File(saved.uri).size };
  });
  if (!small) return "too_big";
  const kept = new File(photosDir(), `${Date.now()}.jpg`);
  await new File(small.uri).move(kept);
  return { uri: kept.uri, name: "foto.jpg", type: "image/jpeg" };
}

export async function cleanupPhotos(db: SQLiteDatabase) {
  const rows = await db.getAllAsync<{ payload: string }>(
    "SELECT payload FROM outbox WHERE kind = 'reports'",
  );
  const files = photosDir()
    .list()
    .filter((entry): entry is File => entry instanceof File);
  const orphans = new Set(
    orphanPhotos(
      files.map((f) => f.uri),
      rows.map((r) => JSON.parse(r.payload)),
    ),
  );
  for (const file of files) if (orphans.has(file.uri)) file.delete();
}
