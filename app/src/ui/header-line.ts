const MONTHS = [
  "ene",
  "feb",
  "mar",
  "abr",
  "may",
  "jun",
  "jul",
  "ago",
  "sep",
  "oct",
  "nov",
  "dic",
];

function laPazParts(iso: string) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/La_Paz",
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(new Date(iso));
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  return {
    day: Number(get("day")),
    month: Number(get("month")),
    time: `${get("hour")}:${get("minute")}`,
  };
}

export function headerLine(
  zoneName: string | null,
  updatedAt: string | null,
): string {
  if (!zoneName || !updatedAt) return "Buscando datos…";
  const { day, month, time } = laPazParts(updatedAt);
  return `${zoneName} · actualizado ${day} ${MONTHS[month - 1]}, ${time}`;
}
