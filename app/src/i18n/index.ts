import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import { es } from "./es";
import { qu } from "./qu";
import type { Language } from "../farm/types";

export function setupI18n(language: Language = "es") {
  if (!i18n.isInitialized)
    void i18n.use(initReactI18next).init({
      resources: { es: { translation: es }, qu: { translation: qu } },
      lng: language,
      fallbackLng: "es",
      interpolation: { escapeValue: false },
    });
  else void i18n.changeLanguage(language);
  return i18n;
}
