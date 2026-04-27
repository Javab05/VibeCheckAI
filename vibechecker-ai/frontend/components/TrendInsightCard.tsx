import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Dimensions } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, FONTS } from '../constants/theme';
import { API_URL } from '../constants/api';

const { width } = Dimensions.get('window');
const CARD_WIDTH = width - SPACING.xl * 2;

interface TrendData {
  trend_summary: string;
  trend_direction: 'improving' | 'declining' | 'stable' | 'insufficient_data';
  count: number;
}

export const TrendInsightCard = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<TrendData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchTrend();
  }, []);

  const fetchTrend = async () => {
    try {
      const userId = await AsyncStorage.getItem('user_id');
      if (!userId) {
        setLoading(false);
        return;
      }

      const response = await fetch(`${API_URL}/trend/${userId}`);
      if (!response.ok) throw new Error('Failed to fetch');
      
      const json = await response.json();
      setData(json);
    } catch (err) {
      console.error('Error fetching trend:', err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={[styles.card, styles.loadingCard]}>
        <ActivityIndicator color={COLORS.amber} />
        <Text style={styles.loadingText}>Analyzing your vibes...</Text>
      </View>
    );
  }

  if (error || !data) {
    return null; // Or a silent failure if we don't want to show an error card
  }

  const isInsufficient = data.trend_direction === 'insufficient_data';

  const getBadgeConfig = () => {
    switch (data.trend_direction) {
      case 'improving':
        return { color: COLORS.moodGreat, icon: 'trending-up', label: 'Improving' };
      case 'declining':
        return { color: COLORS.moodDown, icon: 'trending-down', label: 'Declining' };
      case 'stable':
        return { color: COLORS.textSecondary, icon: 'remove', label: 'Stable' };
      default:
        return { color: COLORS.textMuted, icon: 'help-circle', label: 'Neutral' };
    }
  };

  const badge = getBadgeConfig();

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View>
          <Text style={styles.sectionLabel}>Insights</Text>
          <Text style={styles.cardTitle}>Vibe Trend</Text>
        </View>
        {!isInsufficient && (
          <View style={[styles.badge, { backgroundColor: badge.color + '20', borderColor: badge.color }]}>
            <Ionicons name={badge.icon as any} size={14} color={badge.color} />
            <Text style={[styles.badgeText, { color: badge.color }]}>{badge.label}</Text>
          </View>
        )}
      </View>

      <Text style={[styles.summary, isInsufficient && styles.emptySummary]}>
        {isInsufficient 
          ? "Keep checking in daily — your trend will appear here soon." 
          : data.trend_summary}
      </Text>

      {!isInsufficient && (
        <View style={styles.footer}>
          <Text style={styles.footerText}>Based on {data.count} check-ins</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    width: CARD_WIDTH,
    backgroundColor: COLORS.card,
    borderRadius: RADIUS.xl,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: SPACING.xl,
    marginBottom: SPACING.lg,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 20,
    elevation: 4,
  },
  loadingCard: {
    height: 160,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: COLORS.textSecondary,
    marginTop: SPACING.sm,
    fontSize: FONTS.sizes.sm,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: SPACING.md,
  },
  sectionLabel: {
    color: COLORS.amber,
    fontSize: FONTS.sizes.xs,
    fontWeight: FONTS.weights.bold,
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    marginBottom: SPACING.xs,
  },
  cardTitle: {
    color: COLORS.textPrimary,
    fontSize: FONTS.sizes.xl,
    fontWeight: FONTS.weights.bold,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.sm,
    paddingVertical: 4,
    borderRadius: RADIUS.full,
    borderWidth: 1,
    gap: 4,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: FONTS.weights.bold,
    textTransform: 'uppercase',
  },
  summary: {
    color: COLORS.textPrimary,
    fontSize: FONTS.sizes.md,
    lineHeight: 22,
    marginBottom: SPACING.md,
  },
  emptySummary: {
    color: COLORS.textSecondary,
    fontStyle: 'italic',
  },
  footer: {
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
    paddingTop: SPACING.md,
  },
  footerText: {
    color: COLORS.textMuted,
    fontSize: FONTS.sizes.xs,
    fontWeight: FONTS.weights.medium,
  },
});
