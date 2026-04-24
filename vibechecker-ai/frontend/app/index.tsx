import { View, Text, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { router } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { COLORS, SPACING, RADIUS, FONTS } from '../constants/theme';

const { height } = Dimensions.get('window');

export default function WelcomeScreen() {
  return (
    <View style={styles.root}>
      {/* Ambient glow blobs */}
      <View style={styles.blobTop} />
      <View style={styles.blobBottom} />

      <SafeAreaView style={styles.safe}>
        {/* Logo area */}
        <View style={styles.logoArea}>
          <View style={styles.logoCircle}>
            <Text style={styles.logoEmoji}>🌤️</Text>
          </View>
          <Text style={styles.appName}>VIBE CHECK</Text>
          <Text style={styles.tagline}>Know your seasonal self</Text>
        </View>

        {/* Center illustration */}
        <View style={styles.centerBlock}>
          <Text style={styles.bigEmoji}>🧠</Text>
          <Text style={styles.headline}>AI-powered{'\n'}SAD detection</Text>
          <Text style={styles.subline}>
            Snap a selfie. Answer a few questions.{'\n'}
            Understand your seasonal mood patterns.
          </Text>
        </View>

        {/* Pills */}
        <View style={styles.pillRow}>
          {['📸 Face Scan', '📊 SAD Score', '📅 History'].map((p) => (
            <View key={p} style={styles.pill}>
              <Text style={styles.pillText}>{p}</Text>
            </View>
          ))}
        </View>

        {/* CTAs */}
        <View style={styles.ctaBlock}>
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => router.push('/login')}
          >
            <LinearGradient
              colors={[COLORS.amber, COLORS.coral]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.ctaPrimary}
            >
              <Text style={styles.ctaPrimaryText}>Get Started →</Text>
            </LinearGradient>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.ctaSecondary}
            activeOpacity={0.7}
            onPress={() => router.push('/login')}
          >
            <Text style={styles.ctaSecondaryText}>I already have an account</Text>
          </TouchableOpacity>

          <Text style={styles.disclaimer}>
            Not a medical diagnosis · Always consult a professional
          </Text>
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: COLORS.background },
  safe: { flex: 1, paddingHorizontal: SPACING.xl, justifyContent: 'space-between' },

  blobTop: {
    position: 'absolute', width: 320, height: 320, borderRadius: 160,
    backgroundColor: COLORS.amber, opacity: 0.06, top: -100, right: -100,
  },
  blobBottom: {
    position: 'absolute', width: 240, height: 240, borderRadius: 120,
    backgroundColor: COLORS.steel, opacity: 0.08, bottom: 80, left: -80,
  },

  logoArea: { alignItems: 'center', paddingTop: SPACING.xl },
  logoCircle: {
    width: 64, height: 64, borderRadius: RADIUS.full,
    backgroundColor: COLORS.card, borderWidth: 1, borderColor: COLORS.border,
    alignItems: 'center', justifyContent: 'center', marginBottom: SPACING.md,
  },
  logoEmoji: { fontSize: 32 },
  appName: {
    color: COLORS.amber, fontSize: FONTS.sizes.sm,
    fontWeight: FONTS.weights.black, letterSpacing: 4,
  },
  tagline: { color: COLORS.textSecondary, fontSize: FONTS.sizes.sm, marginTop: 4 },

  centerBlock: { alignItems: 'center' },
  bigEmoji: { fontSize: 80, marginBottom: SPACING.xl },
  headline: {
    color: COLORS.textPrimary, fontSize: FONTS.sizes['4xl'],
    fontWeight: FONTS.weights.black, textAlign: 'center',
    lineHeight: 50, marginBottom: SPACING.base,
  },
  subline: {
    color: COLORS.textSecondary, fontSize: FONTS.sizes.md,
    textAlign: 'center', lineHeight: 22,
  },

  pillRow: { flexDirection: 'row', justifyContent: 'center', gap: SPACING.sm },
  pill: {
    backgroundColor: COLORS.card, borderRadius: RADIUS.full,
    paddingHorizontal: SPACING.md, paddingVertical: SPACING.xs,
    borderWidth: 1, borderColor: COLORS.border,
  },
  pillText: { color: COLORS.textSecondary, fontSize: FONTS.sizes.xs, fontWeight: FONTS.weights.semibold },

  ctaBlock: { paddingBottom: SPACING.md },
  ctaPrimary: {
    borderRadius: RADIUS.full, paddingVertical: SPACING.base + 2,
    alignItems: 'center', marginBottom: SPACING.md,
  },
  ctaPrimaryText: { color: COLORS.white, fontWeight: FONTS.weights.bold, fontSize: FONTS.sizes.base },
  ctaSecondary: {
    borderRadius: RADIUS.full, paddingVertical: SPACING.md,
    alignItems: 'center', borderWidth: 1.5, borderColor: COLORS.border,
    marginBottom: SPACING.lg,
  },
  ctaSecondaryText: { color: COLORS.textSecondary, fontWeight: FONTS.weights.semibold, fontSize: FONTS.sizes.md },
  disclaimer: { color: COLORS.textMuted, fontSize: FONTS.sizes.xs, textAlign: 'center' },
});