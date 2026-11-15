import * as Speech from "expo-speech";

export function speak(text: string) {
  Speech.stop();
  Speech.speak(text, { language: "es-BO", rate: 0.92 });
}
