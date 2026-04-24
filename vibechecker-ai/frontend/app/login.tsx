import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ScrollView, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { COLORS, SPACING, RADIUS, FONTS } from '../constants/theme';

export default function LoginScreen() {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [showPass, setShowPass] = useState(false);

  const handleSubmit = () => {
    // TODO: wire to backend auth
    router.replace('/(tabs)/home');
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Back */}
          <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={20} color={COLORS.textSecondary} />
          </TouchableOpacity>

          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.headerEmoji}>🌤️</Text>
            <Text style={styles.headerTitle}>
              {mode === 'login' ? 'Welcome back' : 'Create account'}
            </Text>
            <Text style={styles.headerSub}>
              {mode === 'login'
                ? 'Sign in to continue your vibe journey'
                : 'Start tracking your seasonal mood today'}
            </Text>
          </View>

          {/* Toggle */}
          <View style={styles.toggle}>
            <TouchableOpacity
              style={[styles.toggleBtn, mode === 'login' && styles.toggleBtnActive]}
              onPress={() => setMode('login')}
            >
              <Text style={[styles.toggleBtnText, mode === 'login' && styles.toggleBtnTextActive]}>
                Log In
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.toggleBtn, mode === 'signup' && styles.toggleBtnActive]}
              onPress={() => setMode('signup')}
            >
              <Text style={[styles.toggleBtnText, mode === 'signup' && styles.toggleBtnTextActive]}>
                Sign Up
              </Text>
            </TouchableOpacity>
          </View>

          {/* Form */}
          <View style={styles.form}>
            {mode === 'signup' && (
              <View style={styles.inputWrapper}>
                <Ionicons name="person-outline" size={18} color={COLORS.textMuted} style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="Full name"
                  placeholderTextColor={COLORS.textMuted}
                  value={name}
                  onChangeText={setName}
                  autoCapitalize="words"
                />
              </View>
            )}

            <View style={styles.inputWrapper}>
              <Ionicons name="mail-outline" size={18} color={COLORS.textMuted} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Email address"
                placeholderTextColor={COLORS.textMuted}
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
              />
            </View>

            <View style={styles.inputWrapper}>
              <Ionicons name="lock-closed-outline" size={18} color={COLORS.textMuted} style={styles.inputIcon} />
              <TextInput
                style={[styles.input, { flex: 1 }]}
                placeholder="Password"
                placeholderTextColor={COLORS.textMuted}
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPass}
              />
              <TouchableOpacity onPress={() => setShowPass(!showPass)} style={styles.eyeBtn}>
                <Ionicons
                  name={showPass ? 'eye-off-outline' : 'eye-outline'}
                  size={18}
                  color={COLORS.textMuted}
                />
              </TouchableOpacity>
            </View>

            {mode === 'login' && (
              <TouchableOpacity style={styles.forgotBtn}>
                <Text style={styles.forgotText}>Forgot password?</Text>
              </TouchableOpacity>
            )}
          </View>

          {/* Submit */}
          <TouchableOpacity onPress={handleSubmit} activeOpacity={0.85}>
            <LinearGradient
              colors={[COLORS.amber, COLORS.coral]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.submitBtn}
            >
              <Text style={styles.submitText}>
                {mode === 'login' ? 'Sign In →' : 'Create Account →'}
              </Text>
            </LinearGradient>
          </TouchableOpacity>

          {/* Divider */}
          <View style={styles.dividerRow}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>or</Text>
            <View style={styles.dividerLine} />
          </View>

          {/* Social logins (frame only) */}
          <TouchableOpacity style={styles.socialBtn} activeOpacity={0.8}>
            <Image source={require('../assets/apple-logo.png')} style={styles.socialImage} />
            <Text style={styles.socialText}>Continue with Apple</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.socialBtn} activeOpacity={0.8}>
            <Image source={require('../assets/google-logo.png')} style={styles.socialImage} />
            <Text style={styles.socialText}>Continue with Google</Text>
          </TouchableOpacity>

          <Text style={styles.legalText}>
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  scroll: { paddingHorizontal: SPACING.xl, paddingBottom: SPACING['3xl'] },

  backBtn: {
    width: 40, height: 40, borderRadius: RADIUS.full,
    backgroundColor: COLORS.card, alignItems: 'center', justifyContent: 'center',
    marginTop: SPACING.base, marginBottom: SPACING.xl,
    borderWidth: 1, borderColor: COLORS.border,
  },

  header: { marginBottom: SPACING['2xl'] },
  headerEmoji: { fontSize: 40, marginBottom: SPACING.md },
  headerTitle: {
    color: COLORS.textPrimary, fontSize: FONTS.sizes['3xl'],
    fontWeight: FONTS.weights.black, marginBottom: SPACING.sm,
  },
  headerSub: { color: COLORS.textSecondary, fontSize: FONTS.sizes.md, lineHeight: 22 },

  toggle: {
    flexDirection: 'row', backgroundColor: COLORS.card,
    borderRadius: RADIUS.full, padding: 4, marginBottom: SPACING.xl,
    borderWidth: 1, borderColor: COLORS.border,
  },
  toggleBtn: { flex: 1, paddingVertical: SPACING.sm, borderRadius: RADIUS.full, alignItems: 'center' },
  toggleBtnActive: { backgroundColor: COLORS.amber },
  toggleBtnText: { color: COLORS.textMuted, fontWeight: FONTS.weights.semibold, fontSize: FONTS.sizes.md },
  toggleBtnTextActive: { color: COLORS.white },

  form: { gap: SPACING.md, marginBottom: SPACING.xl },
  inputWrapper: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: COLORS.card, borderRadius: RADIUS.lg,
    paddingHorizontal: SPACING.base, borderWidth: 1.5, borderColor: COLORS.border,
    minHeight: 54,
  },
  inputIcon: { marginRight: SPACING.sm },
  input: { flex: 1, color: COLORS.textPrimary, fontSize: FONTS.sizes.md, paddingVertical: SPACING.md },
  eyeBtn: { padding: SPACING.sm },
  forgotBtn: { alignSelf: 'flex-end' },
  forgotText: { color: COLORS.amber, fontSize: FONTS.sizes.sm, fontWeight: FONTS.weights.medium },

  submitBtn: {
    borderRadius: RADIUS.full, paddingVertical: SPACING.base + 2,
    alignItems: 'center', marginBottom: SPACING.xl,
  },
  submitText: { color: COLORS.white, fontWeight: FONTS.weights.bold, fontSize: FONTS.sizes.base },

  dividerRow: { flexDirection: 'row', alignItems: 'center', gap: SPACING.md, marginBottom: SPACING.lg },
  dividerLine: { flex: 1, height: 1, backgroundColor: COLORS.border },
  dividerText: { color: COLORS.textMuted, fontSize: FONTS.sizes.sm },

  socialBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: SPACING.sm, backgroundColor: COLORS.card, borderRadius: RADIUS.lg,
    paddingVertical: SPACING.base, marginBottom: SPACING.sm,
    borderWidth: 1, borderColor: COLORS.border,
  },
  socialBtnEmoji: { fontSize: 20 },
  socialBtnText: { color: COLORS.textPrimary, fontWeight: FONTS.weights.semibold, fontSize: FONTS.sizes.md },

  legalText: {
    color: COLORS.textMuted, fontSize: FONTS.sizes.xs,
    textAlign: 'center', lineHeight: 16, marginTop: SPACING.xl,
  },

  socialImage: {
  width: 20,
  height: 20,
  resizeMode: 'contain',
},
});