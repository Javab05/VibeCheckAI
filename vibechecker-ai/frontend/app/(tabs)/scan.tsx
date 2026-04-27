import AsyncStorage from '@react-native-async-storage/async-storage';
import { useState, useEffect } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet,
  Dimensions, ActivityIndicator, Image, ScrollView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { COLORS, SPACING, RADIUS, FONTS } from '../../constants/theme';
import { API_URL } from '../../constants/api';

const { width } = Dimensions.get('window');
const PREVIEW_SIZE = width * 0.78;

type ScanState = 'idle' | 'scanning' | 'done';

type InferenceResult = {
  vibe_score: number;
  dominant_emotion: string;
  confidence: number;
};

export default function HomeScreen() {
  const [scanState, setScanState] = useState<ScanState>('idle');
  const [capturedUri, setCapturedUri] = useState<string | null>(null);
  const [result, setResult] = useState<InferenceResult | null>(null);

  useEffect(() => {
    const requestPermissions = async () => {
      await ImagePicker.requestMediaLibraryPermissionsAsync();
      await ImagePicker.requestCameraPermissionsAsync();
    };
    requestPermissions();
  }, []);

  // ── Helper: Get vibe level label based on score ───────────
  const getVibeLevel = (score: number) => {
    if (score >= 80) return 'GREAT';
    if (score >= 60) return 'GOOD';
    if (score >= 40) return 'OKAY';
    if (score >= 20) return 'LOW';
    return 'DOWN';
  };

  // ── Run ML scan ───────────────────────────────────────────
  const runScan = async (uri: string) => {
    const userId = await AsyncStorage.getItem('user_id');
    
    if (!userId) {
      alert('Please log in first to save your vibe check!');
      return;
    }

    setCapturedUri(uri);
    setScanState('scanning');

    try {
      const formData = new FormData();
      formData.append('user_id', userId);

      if (Platform.OS === 'web') {
        const response = await fetch(uri);
        const blob = await response.blob();
        formData.append('image', blob, 'selfie.jpg');
      } else {
        formData.append('image', {
          uri: uri,
          type: 'image/jpeg',
          name: 'selfie.jpg',
        } as any);
      }

      const response = await fetch(`${API_URL}/inference`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setResult({
          vibe_score: data.vibe_score,
          dominant_emotion: data.dominant_emotion,
          confidence: Math.round(data.confidence * 100),
        });
        setScanState('done');
      } else {
        alert(data.error || 'Something went wrong');
        setScanState('idle');
      }
    } catch (error) {
      alert('Cannot connect to server. Make sure backend is running!');
      setScanState('idle');
    }
  };

  // ── Pick from gallery ─────────────────────────────────────
  const handlePickFromGallery = async () => {
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.85,
      allowsEditing: true,
      aspect: [1, 1],
    });
    if (!res.canceled && res.assets[0]) {
      runScan(res.assets[0].uri);
    }
  };

  // ── Take photo with camera ────────────────────────────────
  const handleTakePhoto = async () => {
    const res = await ImagePicker.launchCameraAsync({
      cameraType: ImagePicker.CameraType.front,
      quality: 0.85,
      allowsEditing: true,
      aspect: [1, 1],
    });
    if (!res.canceled && res.assets[0]) {
      runScan(res.assets[0].uri);
    }
  };

  const handleReset = () => {
    setScanState('idle');
    setCapturedUri(null);
    setResult(null);
  };

  // ── Helper: Get color based on score ────────────────────────
  const getVibeColor = (score: number) => {
    if (score >= 70) return COLORS.moodGreat;
    if (score >= 40) return COLORS.moodOkay;
    return COLORS.moodDown;
  };

  // ── Result view ───────────────────────────────────────────
  if (scanState === 'done' && result) {
    const scoreColor = getVibeColor(result.vibe_score);
    const vibeLevel = getVibeLevel(result.vibe_score);

    return (
      <SafeAreaView style={styles.safe}>
        <ScrollView contentContainerStyle={styles.resultScroll} showsVerticalScrollIndicator={false}>

          <Text style={styles.resultHeader}>Vibe Check Result ✓</Text>

          {/* Photo preview */}
          {capturedUri && (
            <View style={styles.resultImageWrap}>
              <Image source={{ uri: capturedUri }} style={styles.resultImage} />
              <View style={styles.analyzedBadge}>
                <Text style={styles.analyzedBadgeText}>Analyzed</Text>
              </View>
            </View>
          )}

          {/* Score ring */}
          <View style={styles.scoreBlock}>
            <View style={[styles.scoreRingOuter, { borderColor: scoreColor + '55' }]}>
              <View style={[styles.scoreRingInner, { borderColor: scoreColor }]}>
                <Text style={styles.scoreNum}>{Math.round(result.vibe_score)}</Text>
                <Text style={styles.scoreMax}>/100</Text>
              </View>
            </View>
            <Text style={[styles.scoreLevel, {color: scoreColor}]}>
              {vibeLevel}
            </Text>
            <Text style={styles.scoreConf}>Model confidence: {result.confidence}%</Text>

            {/* Visual Indicator - Bar */}
            <View style={styles.barContainer}>
              <View 
                style={[
                  styles.barFill, 
                  { 
                    width: `${result.vibe_score}%`, 
                    backgroundColor: scoreColor 
                  }
                ]} 
              />
            </View>
          </View>

          {/* Disclaimer */}
          <View style={styles.disclaimerBox}>
            <Ionicons name="information-circle-outline" size={14} color={COLORS.steel} />
            <Text style={styles.disclaimerText}>
              This is not a medical diagnosis. Please consult a healthcare professional if you are concerned.
            </Text>
          </View>

          {/* Actions */}
          <TouchableOpacity onPress={handleReset} activeOpacity={0.85}>
            <LinearGradient
              colors={[COLORS.amber, COLORS.coral]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.scanAgainBtn}
            >
              <Ionicons name="camera" size={18} color={COLORS.white} />
              <Text style={styles.scanAgainText}>Scan Again</Text>
            </LinearGradient>
          </TouchableOpacity>

        </ScrollView>
      </SafeAreaView>
    );
  }

  // ── Scanning view ─────────────────────────────────────────
  if (scanState === 'scanning') {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.scanningContainer}>
          {capturedUri && (
            <Image source={{ uri: capturedUri }} style={styles.scanningImage} />
          )}
          <View style={styles.scanningOverlay}>
            <ActivityIndicator size="large" color={COLORS.amber} />
            <Text style={styles.scanningText}>Analyzing your vibe...</Text>
            <Text style={styles.scanningSubText}>Reading facial expression patterns</Text>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  // ── Idle / Upload view ────────────────────────────────────
  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>

        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerLabel}>DAILY SCAN</Text>
          <Text style={styles.headerTitle}>Vibe Check</Text>
        </View>

        {/* Upload area */}
        <View style={styles.uploadArea}>
          <View style={styles.uploadCircle}>
            <Ionicons name="person-outline" size={80} color={COLORS.textMuted} />
          </View>
          <Text style={styles.uploadTitle}>Take or upload a selfie</Text>
          <Text style={styles.uploadSub}>
            Our AI will analyze your facial expression{'\n'}to detect signs of seasonal mood changes
          </Text>
        </View>

        {/* Buttons */}
        <View style={styles.btnGroup}>
          {/* Camera button */}
          <TouchableOpacity onPress={handleTakePhoto} activeOpacity={0.85}>
            <LinearGradient
              colors={[COLORS.amber, COLORS.coral]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.primaryBtn}
            >
              <Ionicons name="camera" size={22} color={COLORS.white} />
              <Text style={styles.primaryBtnText}>Take a Selfie</Text>
            </LinearGradient>
          </TouchableOpacity>

          {/* Upload button */}
          <TouchableOpacity
            style={styles.secondaryBtn}
            onPress={handlePickFromGallery}
            activeOpacity={0.8}
          >
            <Ionicons name="images-outline" size={22} color={COLORS.amber} />
            <Text style={styles.secondaryBtnText}>Upload from Gallery</Text>
          </TouchableOpacity>
        </View>

        {/* Privacy note */}
        <View style={styles.privacyRow}>
          <Ionicons name="shield-checkmark-outline" size={14} color={COLORS.textMuted} />
          <Text style={styles.privacyText}>
            Your photo is only used for SAD analysis and is never stored or shared.
          </Text>
        </View>

      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },

  // Idle
  container: {
    flex: 1, paddingHorizontal: SPACING.xl,
    justifyContent: 'space-between', paddingBottom: SPACING.xl,
  },
  header: { paddingTop: SPACING.lg },
  headerLabel: {
    color: COLORS.textMuted, fontSize: FONTS.sizes.xs,
    fontWeight: FONTS.weights.bold, letterSpacing: 1.5, marginBottom: 4,
  },
  headerTitle: {
    color: COLORS.textPrimary, fontSize: FONTS.sizes['3xl'],
    fontWeight: FONTS.weights.black,
  },

  uploadArea: { alignItems: 'center', flex: 1, justifyContent: 'center' },
  uploadCircle: {
    width: PREVIEW_SIZE, height: PREVIEW_SIZE,
    borderRadius: PREVIEW_SIZE / 2,
    backgroundColor: COLORS.card,
    borderWidth: 2, borderColor: COLORS.border,
    borderStyle: 'dashed',
    alignItems: 'center', justifyContent: 'center',
    marginBottom: SPACING.xl,
  },
  uploadTitle: {
    color: COLORS.textPrimary, fontSize: FONTS.sizes.xl,
    fontWeight: FONTS.weights.bold, textAlign: 'center',
    marginBottom: SPACING.sm,
  },
  uploadSub: {
    color: COLORS.textSecondary, fontSize: FONTS.sizes.md,
    textAlign: 'center', lineHeight: 22,
  },

  btnGroup: { gap: SPACING.md, marginBottom: SPACING.lg },
  primaryBtn: {
    borderRadius: RADIUS.full, paddingVertical: SPACING.base + 2,
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'center', gap: SPACING.sm,
  },
  primaryBtnText: {
    color: COLORS.white, fontWeight: FONTS.weights.bold,
    fontSize: FONTS.sizes.base,
  },
  secondaryBtn: {
    borderRadius: RADIUS.full, paddingVertical: SPACING.base + 2,
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'center', gap: SPACING.sm,
    borderWidth: 1.5, borderColor: COLORS.amber,
  },
  secondaryBtnText: {
    color: COLORS.amber, fontWeight: FONTS.weights.bold,
    fontSize: FONTS.sizes.base,
  },

  privacyRow: {
    flexDirection: 'row', alignItems: 'flex-start',
    gap: SPACING.sm, paddingHorizontal: SPACING.sm,
  },
  privacyText: {
    color: COLORS.textMuted, fontSize: FONTS.sizes.xs,
    flex: 1, lineHeight: 16,
  },

  // Scanning
  scanningContainer: {
    flex: 1, alignItems: 'center', justifyContent: 'center',
  },
  scanningImage: {
    width: PREVIEW_SIZE, height: PREVIEW_SIZE,
    borderRadius: PREVIEW_SIZE / 2,
    position: 'absolute', opacity: 0.4,
  },
  scanningOverlay: { alignItems: 'center', gap: SPACING.md },
  scanningText: {
    color: COLORS.textPrimary, fontSize: FONTS.sizes.lg,
    fontWeight: FONTS.weights.bold,
  },
  scanningSubText: { color: COLORS.textSecondary, fontSize: FONTS.sizes.sm },

  // Results
  resultScroll: { paddingHorizontal: SPACING.xl, paddingBottom: SPACING['3xl'] },
  resultHeader: {
    color: COLORS.textPrimary, fontSize: FONTS.sizes['2xl'],
    fontWeight: FONTS.weights.black, paddingVertical: SPACING.lg,
  },
  resultImageWrap: { alignSelf: 'center', marginBottom: SPACING.xl, position: 'relative' },
  resultImage: {
    width: 130, height: 130, borderRadius: 65,
    borderWidth: 3, borderColor: COLORS.amber,
  },
  analyzedBadge: {
    position: 'absolute', bottom: -10, alignSelf: 'center',
    backgroundColor: COLORS.amber, borderRadius: RADIUS.full,
    paddingHorizontal: SPACING.sm, paddingVertical: 3,
  },
  analyzedBadgeText: {
    color: COLORS.white, fontSize: FONTS.sizes.xs,
    fontWeight: FONTS.weights.bold,
  },

  scoreBlock: { alignItems: 'center', marginBottom: SPACING.xl },
  scoreRingOuter: {
    width: 130, height: 130, borderRadius: 65,
    borderWidth: 5, borderColor: COLORS.moodLow + '55',
    alignItems: 'center', justifyContent: 'center', marginBottom: SPACING.md,
  },
  scoreRingInner: {
    width: 100, height: 100, borderRadius: 50,
    borderWidth: 4, borderColor: COLORS.moodLow,
    alignItems: 'center', justifyContent: 'center',
    backgroundColor: COLORS.surface,
  },
  scoreNum: {
    color: COLORS.textPrimary, fontSize: FONTS.sizes['3xl'],
    fontWeight: FONTS.weights.black,
  },
  scoreMax: { color: COLORS.textMuted, fontSize: FONTS.sizes.xs },
  scoreLevel: { fontSize: FONTS.sizes.xl, fontWeight: FONTS.weights.bold, marginBottom: 4 },
  scoreConf: { color: COLORS.textMuted, fontSize: FONTS.sizes.sm },

  barContainer: {
    width: '100%',
    height: 12,
    backgroundColor: COLORS.card,
    borderRadius: RADIUS.full,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: COLORS.border,
    marginTop: SPACING.lg,
  },
  barFill: {
    height: '100%',
    borderRadius: RADIUS.full,
  },

  signalsBox: {
    backgroundColor: COLORS.card, borderRadius: RADIUS.xl,
    padding: SPACING.base, marginBottom: SPACING.lg,
    borderWidth: 1, borderColor: COLORS.border, gap: SPACING.sm,
  },
  signalsTitle: {
    color: COLORS.textMuted, fontSize: FONTS.sizes.xs,
    fontWeight: FONTS.weights.bold, letterSpacing: 1.2, marginBottom: SPACING.xs,
  },
  signalRow: { flexDirection: 'row', alignItems: 'center', gap: SPACING.sm },
  signalDot: { width: 8, height: 8, borderRadius: RADIUS.full },
  signalText: { color: COLORS.textPrimary, fontSize: FONTS.sizes.md },

  disclaimerBox: {
    flexDirection: 'row', alignItems: 'flex-start', gap: SPACING.sm,
    backgroundColor: COLORS.steelDeep + '22', borderRadius: RADIUS.md,
    padding: SPACING.md, marginBottom: SPACING.xl,
    borderWidth: 1, borderColor: COLORS.steelDeep + '44',
  },
  disclaimerText: { color: COLORS.steelLight, fontSize: FONTS.sizes.xs, flex: 1, lineHeight: 16 },

  scanAgainBtn: {
    borderRadius: RADIUS.full, paddingVertical: SPACING.base + 2,
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'center', gap: SPACING.sm,
  },
  scanAgainText: { color: COLORS.white, fontWeight: FONTS.weights.bold, fontSize: FONTS.sizes.base },
});