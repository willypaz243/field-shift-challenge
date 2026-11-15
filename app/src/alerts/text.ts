import type { TFunction } from "i18next";
import type { Alert } from "./alerts";
import { weekday } from "../ui/dates";

const capital = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

export function alertWhen(a: Alert, t: TFunction) {
  if (!a.fecha_evento) return t("avisos.esta_semana");
  const day = `${capital(weekday(a.fecha_evento))} ${Number(a.fecha_evento.slice(8))}`;
  return a.momento === "madrugada" ? `${day}, ${t("avisos.madrugada")}` : day;
}

export function alertTitle(a: Alert, t: TFunction) {
  return t(`avisos.tipo.${a.tipo}`, { defaultValue: capital(a.tipo) });
}

export function alertDetail(a: Alert, t: TFunction) {
  const parts: string[] = [];
  if (a.tipo === "represa_baja" && a.valor?.nivel_pct != null)
    parts.push(
      t("avisos.represa_detalle", { nivel: Math.round(a.valor.nivel_pct) }),
    );
  if (a.valor?.tmin != null)
    parts.push(t("avisos.helada_detalle", { tmin: Math.round(a.valor.tmin) }));
  if (a.confianza === "baja") parts.push(t("avisos.poco_seguro"));
  if (a.volver_a_avisar)
    parts.push(t("avisos.volver", { dia: weekday(a.volver_a_avisar) }));
  return parts.join(" ");
}

export function notificationText(a: Alert, t: TFunction) {
  return {
    title: t("avisos.notificacion", {
      tipo: alertTitle(a, t),
      dia: a.fecha_evento ? weekday(a.fecha_evento) : "",
    }),
    body: alertDetail(a, t) || alertTitle(a, t),
  };
}
