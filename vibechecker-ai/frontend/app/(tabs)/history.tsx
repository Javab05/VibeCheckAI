import { useState, useEffect, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity,
  StyleSheet, ActivityIndicator, RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../../constants/api';
import { COLORS, SPACING, RADIUS, FONTS } from '../../constants/theme';
import VibeGraph from '../../src/components/VibeGraph';

type CheckinEntry = {
  checkin_id: number;
  captured_at: string;
  season: string;
  emotion: string | null;
  confidence: number | null;
  scores: Record<string, number> | null;
};

const SEASONS = ['winter', 'spring', 'summer', 'fall'];
const SEASON_EMOJIS: Record<string, string> = {
  winter: '', spring: '', summer: '', fall: '',
};

const getEmotionColor = (emotion: string | null) => {
  if (!emotion) return COLORS.textMuted;
  const map: Record<string, string> = {
    happy: COLORS.moodGreat,
    sad: COLORS.moodDown,
    angry: COLORS.error,
    fear: COLORS.moodLow,
    disgust: COLORS.moodLow,
    surprise: COLORS.moodOkay,
    neutral: COLORS.textSecondary,
  };
  return map[emotion] ?? COLORS.textSecondary;
};

const getEmotionEmoji = (emotion: string | null) => {
  if (!emotion) return '❓';
  const map: Record<string, string> = {
    happy: '😄', sad: '😢', angry: '😠',
    fear: '😨', disgust: '🤢', surprise: '😲', neutral: '😐',
  };
  return map[emotion] ?? '😐';
};

const getCurrentSeason = () => {
  const month = new Date().getMonth() + 1;
  if (month <= 2 || month === 12) return 'winter';
  if (month <= 5) return 'spring';
  if (month <= 8) return 'summer';
  return 'fall';
};

const formatDate = (dateStr: string) => {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  } catch { return dateStr; }
};

export default function HistoryScreen() {
  const [checkins, setCheckins] = useState<CheckinEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [season, setSeason] = useState(getCurrentSeason());
  const [year] = useState(new Date().getFullYear());
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = useCallback(async () => {
    try {
      const userId = await AsyncStorage.getItem('user_id');
      if (!userId) { setError('Not logged in'); setLoading(false); return; }

      const response = await fetch(
        `${API_URL}/history/${userId}?season=${season}&season_year=${year}`
      );

      if (!response.ok) throw new Error('Failed to fetch history');

      const data = await response.json();
      setCheckins(data);
      setError(null);
    } catch (e) {
      setError('Could not load history. Make sure backend is running!');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [season, year]);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  const onRefresh = () => { setRefreshing(true); fetchHistory(); };

  // Stats
  const totalCheckins = checkins.length;
  const emotionCounts = checkins.reduce((acc, c) => {
    if (c.emotion) acc[c.emotion] = (acc[c.emotion] ?? 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  const dominantEmotion = Object.entries(emotionCounts).sort((a, b) => b[1] - a[1])[0]?.[0];
  const avgSadness = checkins.length > 0
    ? checkins.reduce((sum, c) => sum + (c.scores?.sad ?? 0), 0) / checkins.length
    : 0;

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.amber} />}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerLabel}>YOUR JOURNEY</Text>
          <Text style={styles.headerTitle}>History</Text>
        </View>

        {/* Season filter */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.seasonScroll}>
          {SEASONS.map(s => (
            <TouchableOpacity
              key={s}
              style={[styles.seasonChip, season === s && styles.seasonChipActive]}
              onPress={() => { setSeason(s); setLoading(true); }}
            >

              <Text style={[styles.seasonLabel, season === s && styles.seasonLabelActive]}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Stats row */}
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Text style={styles.statEmoji}>📸</Text>
            <Text style={styles.statValue}>{totalCheckins}</Text>
            <Text style={styles.statLabel}>Scans</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statEmoji}>{getEmotionEmoji(dominantEmotion)}</Text>
            <Text style={styles.statValue}>{dominantEmotion ?? 'N/A'}</Text>
            <Text style={styles.statLabel}>Top Emotion</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statEmoji}>😢</Text>
            <Text style={[styles.statValue, { color: avgSadness > 0.3 ? COLORS.moodDown : COLORS.moodGreat }]}>
              {Math.round(avgSadness * 100)}%
            </Text>
            <Text style={styles.statLabel}>Avg Sadness</Text>
          </View>
        </View>

        {/* SAD warning */}
        {avgSadness > 0.3 && totalCheckins > 0 && (
          <View style={styles.warningBox}>
            <Ionicons name="warning-outline" size={16} color={COLORS.moodDown} />
            <Text style={styles.warningText}>
              High sadness detected this {season}. Consider speaking with a professional.
            </Text>
          </View>
        )}

        {/* Graph */}
        {checkins.length > 0 && (
          <VibeGraph 
            scores={checkins.map(c => ({
              date: new Date(c.captured_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
              vibe_score: c.scores?.vibe_score ?? Math.round((1 - (c.scores?.sad ?? 0)) * 100),
              dominant_emotion: c.emotion || 'neutral'
            })).reverse()} 
          />
        )}

        {/* Entries */}
        <Text style={styles.sectionTitle}>
            {season.charAt(0).toUpperCase() + season.slice(1)} {year}
        </Text>

        {loading ? (
          <ActivityIndicator size="large" color={COLORS.amber} style={{ marginTop: SPACING['2xl'] }} />
        ) : error ? (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryBtn} onPress={fetchHistory}>
              <Text style={styles.retryBtnText}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : checkins.length === 0 ? (
          <View style={styles.emptyBox}>
            <Text style={styles.emptyEmoji}>🌤️</Text>
            <Text style={styles.emptyTitle}>No scans yet</Text>
            <Text style={styles.emptySub}>Take your first scan to start tracking your vibe!</Text>
          </View>
        ) : (
          checkins.map((entry) => (
            <View key={entry.checkin_id} style={styles.entryCard}>
              <View style={[styles.entryBar, { backgroundColor: getEmotionColor(entry.emotion) }]} />
              <View style={styles.entryLeft}>
                <Text style={styles.entryEmoji}>{getEmotionEmoji(entry.emotion)}</Text>
                <View>
                  <Text style={styles.entryEmotion}>
                    {entry.emotion ? entry.emotion.charAt(0).toUpperCase() + entry.emotion.slice(1) : 'Unknown'}
                  </Text>
                  <Text style={styles.entryDate}>{formatDate(entry.captured_at)}</Text>
                </View>
              </View>
              <View style={styles.entryRight}>
                <Text style={[styles.entryConfidence, { color: getEmotionColor(entry.emotion) }]}>
                  {entry.confidence ? `${Math.round(entry.confidence * 100)}%` : '--'}
                </Text>
                <Text style={styles.entryConfidenceLabel}>confidence</Text>
              </View>
            </View>
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  scroll: { paddingHorizontal: SPACING.base, paddingBottom: SPACING['3xl'] },

  header: { paddingVertical: SPACING.lg },
  headerLabel: { color: COLORS.textMuted, fontSize: FONTS.sizes.xs, fontWeight: FONTS.weights.bold, letterSpacing: 1.5, marginBottom: 4 },
  headerTitle: { color: COLORS.textPrimary, fontSize: FONTS.sizes['3xl'], fontWeight: FONTS.weights.black },

  seasonScroll: { marginBottom: SPACING.lg },
  seasonChip: {
    flexDirection: 'row', alignItems: 'center', gap: SPACING.xs,
    backgroundColor: COLORS.card, borderRadius: RADIUS.full,
    paddingHorizontal: SPACING.base, paddingVertical: SPACING.sm,
    marginRight: SPACING.sm, borderWidth: 1, borderColor: COLORS.border,
  },
  seasonChipActive: { backgroundColor: COLORS.amber, borderColor: COLORS.amber },
  seasonEmoji: { fontSize: 16 },
  seasonLabel: { color: COLORS.textSecondary, fontSize: FONTS.sizes.sm, fontWeight: FONTS.weights.semibold },
  seasonLabelActive: { color: COLORS.white },

  statsRow: { flexDirection: 'row', gap: SPACING.sm, marginBottom: SPACING.lg },
  statCard: {
    flex: 1, backgroundColor: COLORS.card, borderRadius: RADIUS.lg,
    padding: SPACING.md, alignItems: 'center', gap: 4,
    borderWidth: 1, borderColor: COLORS.border,
  },
  statEmoji: { fontSize: 22 },
  statValue: { color: COLORS.amber, fontSize: FONTS.sizes.lg, fontWeight: FONTS.weights.black },
  statLabel: { color: COLORS.textSecondary, fontSize: FONTS.sizes.xs, textAlign: 'center' },

  warningBox: {
    flexDirection: 'row', alignItems: 'flex-start', gap: SPACING.sm,
    backgroundColor: COLORS.moodDown + '18', borderRadius: RADIUS.lg,
    padding: SPACING.base, marginBottom: SPACING.lg,
    borderWidth: 1, borderColor: COLORS.moodDown + '44',
  },
  warningText: { color: COLORS.moodDown, fontSize: FONTS.sizes.sm, flex: 1, lineHeight: 18 },

  sectionTitle: { color: COLORS.textPrimary, fontSize: FONTS.sizes.lg, fontWeight: FONTS.weights.bold, marginBottom: SPACING.md },

  errorBox: { alignItems: 'center', marginTop: SPACING['2xl'], gap: SPACING.md },
  errorText: { color: COLORS.error, fontSize: FONTS.sizes.md, textAlign: 'center' },
  retryBtn: { backgroundColor: COLORS.card, borderRadius: RADIUS.full, paddingHorizontal: SPACING.xl, paddingVertical: SPACING.sm, borderWidth: 1, borderColor: COLORS.border },
  retryBtnText: { color: COLORS.textPrimary, fontWeight: FONTS.weights.semibold },

  emptyBox: { alignItems: 'center', marginTop: SPACING['3xl'], gap: SPACING.md },
  emptyEmoji: { fontSize: 60 },
  emptyTitle: { color: COLORS.textPrimary, fontSize: FONTS.sizes.xl, fontWeight: FONTS.weights.bold },
  emptySub: { color: COLORS.textSecondary, fontSize: FONTS.sizes.md, textAlign: 'center' },

  entryCard: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.card,
    borderRadius: RADIUS.lg, marginBottom: SPACING.sm,
    overflow: 'hidden', borderWidth: 1, borderColor: COLORS.border,
    paddingRight: SPACING.base,
  },
  entryBar: { width: 4, alignSelf: 'stretch' },
  entryLeft: { flexDirection: 'row', alignItems: 'center', gap: SPACING.md, flex: 1, padding: SPACING.base },
  entryEmoji: { fontSize: 28 },
  entryEmotion: { color: COLORS.textPrimary, fontSize: FONTS.sizes.md, fontWeight: FONTS.weights.semibold },
  entryDate: { color: COLORS.textMuted, fontSize: FONTS.sizes.xs, marginTop: 2 },
  entryRight: { alignItems: 'flex-end' },
  entryConfidence: { fontSize: FONTS.sizes.lg, fontWeight: FONTS.weights.black },
  entryConfidenceLabel: { color: COLORS.textMuted, fontSize: FONTS.sizes.xs },
});

