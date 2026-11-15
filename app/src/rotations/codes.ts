const MONTHS: Record<string, string> = {
  ene: "enero",
  feb: "febrero",
  mar: "marzo",
  abr: "abril",
  may: "mayo",
  jun: "junio",
  jul: "julio",
  ago: "agosto",
  sep: "septiembre",
  oct: "octubre",
  nov: "noviembre",
  dic: "diciembre",
};

export type ParsedCode = {
  key: string;
  values?: Record<string, string>;
} | null;

// Codes with a variable part: "heladas_may_ago" (months), "poca_lluvia_abr_sep"
// and "precio_haba" (crop id). Everything else is a plain translation key.
export function parseCode(code: string): ParsedCode {
  const range = /^(heladas|poca_lluvia)_([a-z]{3})(?:_([a-z]{3}))?$/.exec(code);
  if (range && MONTHS[range[2]] && (!range[3] || MONTHS[range[3]]))
    return {
      key: range[3] ? `${range[1]}_rango` : `${range[1]}_mes`,
      values: {
        desde: MONTHS[range[2]],
        ...(range[3] ? { hasta: MONTHS[range[3]] } : {}),
      },
    };
  const price = /^precio_(.+)$/.exec(code);
  if (price) return { key: "precio", values: { cultivo: price[1] } };
  return null;
}
