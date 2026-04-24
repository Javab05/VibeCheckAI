export const COLORS = {
  // Backgrounds
  background: '#0A0A0F',
  surface: '#13131A',
  card: '#1C1C28',
  cardAlt: '#1A1A24',

  // Brand — warm amber sun vs cold steel winter
  amber: '#F5A623',
  amberLight: '#FFC75A',
  amberDeep: '#D4881A',
  coral: '#E8604A',

  // SAD cold tones
  steel: '#5B8DB8',
  steelLight: '#89B4D4',
  steelDeep: '#3A6B96',

  // Mood spectrum
  moodGreat: '#4ADE80',
  moodGood: '#A3E635',
  moodOkay: '#FACC15',
  moodLow: '#FB923C',
  moodDown: '#F87171',

  // Text
  textPrimary: '#F0EEF8',
  textSecondary: '#8886A4',
  textMuted: '#3E3C58',

  // Borders
  border: '#252538',
  divider: '#1A1A28',

  // Utility
  white: '#FFFFFF',
  black: '#000000',
  transparent: 'transparent',
  overlay: 'rgba(0,0,0,0.7)',
  success: '#4ADE80',
  error: '#F87171',
  warning: '#FACC15',
};

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 20,
  xl: 24,
  '2xl': 32,
  '3xl': 48,
  '4xl': 64,
};

export const RADIUS = {
  sm: 8,
  md: 12,
  lg: 18,
  xl: 24,
  '2xl': 36,
  full: 9999,
};

export const FONTS = {
  sizes: {
    xs: 10,
    sm: 12,
    md: 14,
    base: 16,
    lg: 18,
    xl: 22,
    '2xl': 28,
    '3xl': 34,
    '4xl': 42,
    '5xl': 54,
  },
  weights: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
    extrabold: '800' as const,
    black: '900' as const,
  },
};