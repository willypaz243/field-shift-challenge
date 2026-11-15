// Tokens from DESIGN.md (frontmatter is the source of truth).
export const Colors = {
  field: '#1B6E3A',
  fieldDeep: '#145730',
  fieldSoft: '#E8F3EA',
  fieldLine: '#B9D9C1',
  paper: '#FFFFFF',
  paper2: '#F4F7F3',
  line: '#E1E8E0',
  ink: '#13261A',
  ink2: '#33463A',
  cornGold: '#C9A227',
  water: '#1C63B7',
  waterSoft: '#E8F0FB',
  frost: '#0B6E8A',
  frostSoft: '#E2F3F7',
  dry: '#8F5200',
  drySoft: '#FFF3DC',
  nowater: '#B42318',
  nowaterSoft: '#FDECEA',
};

const regular = 'AtkinsonHyperlegibleNext-Regular';
const bold = 'AtkinsonHyperlegibleNext-Bold';

export const Typography = {
  headline: { fontFamily: bold, fontSize: 26, lineHeight: 30, letterSpacing: -0.5 },
  title: { fontFamily: bold, fontSize: 20, lineHeight: 24, letterSpacing: -0.2 },
  body: { fontFamily: regular, fontSize: 19, lineHeight: 27 },
  label: { fontFamily: bold, fontSize: 17, lineHeight: 22 },
  meta: { fontFamily: bold, fontSize: 15, lineHeight: 20 },
};

export const Radius = { btn: 14, card: 16, sheet: 24, pill: 999 };

export const Spacing = { gutter: 16, section: 16, cardPad: 16 };

export const Motion = {
  pressScale: 0.97,
  pressMs: 140,
  sheetMs: 320,
  easeOut: [0.23, 1, 0.32, 1] as const,
  drawer: [0.32, 0.72, 0, 1] as const,
};

export const Touch = { minTarget: 56, buttonHeight: 60 };
