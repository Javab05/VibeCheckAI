import React, { useState, useEffect, useRef } from 'react';
import { View, Text, ActivityIndicator, StyleSheet, Dimensions, TouchableOpacity, ScrollView, Platform } from 'react-native';
// Removed recharts completely. Replaced with react-native-chart-kit
import { LineChart } from 'react-native-chart-kit';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../../constants/api';
import { COLORS, SPACING, RADIUS, FONTS } from '../../constants/theme';

const CHART_HEIGHT = 220;
const Y_AXIS_WIDTH = 45;

const getVibeColor = (score) => {
  if (score > 60) return COLORS.moodGreat;
  if (score >= 40) return COLORS.moodOkay;
  return COLORS.moodDown;
};

const getTrendColor = (direction) => {
  switch (direction) {
    case 'improving': return COLORS.moodGreat;
    case 'declining': return COLORS.moodDown;
    case 'stable': return COLORS.textSecondary;
    default: return COLORS.textMuted;
  }
};

export default function VibeGraph({ scores: initialScores }) {
  const [scores, setScores] = useState(initialScores || []);
  const [loading, setLoading] = useState(!initialScores);
  const [error, setError] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summary, setSummary] = useState(null);
  const scrollViewRef = useRef(null);

  useEffect(() => {
    if (!initialScores) {
      fetchScores();
    } else {
      setScores(initialScores);
    }
  }, [initialScores]);

  // Scroll to end when scores are loaded
  useEffect(() => {
    if (scores.length > 0 && scrollViewRef.current) {
      setTimeout(() => {
        scrollViewRef.current.scrollToEnd({ animated: true });
      }, 500);
    }
  }, [scores]);

  const fetchScores = async () => {
    try {
      const userId = await AsyncStorage.getItem('user_id');
      if (!userId) {
        setError('User not logged in');
        setLoading(false);
        return;
      }

      const response = await fetch(`${API_URL}/history/${userId}`);
      if (!response.ok) throw new Error('Failed to fetch history');

      const data = await response.json();

      const transformedData = data.map(item => {
        let vibeScore = item.scores?.vibe_score;

        if (vibeScore === undefined || vibeScore === null) {
            const happy = item.scores?.happy ?? 0;
            const sad = item.scores?.sad ?? 0;
            vibeScore = Math.round((happy - sad) * 50 + 50);
        }

        return {
          captured_at: item.captured_at,
          date: new Date(item.captured_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          vibe_score: vibeScore,
          dominant_emotion: item.emotion || 'neutral'
        };
      });

      // Sort by captured_at ascending to ensure chronological order
      transformedData.sort((a, b) => new Date(a.captured_at) - new Date(b.captured_at));

      setScores(transformedData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchYearSummary = async () => {
    setSummaryLoading(true);
    try {
      const userId = await AsyncStorage.getItem('user_id');
      if (!userId) return;

      const currentYear = new Date().getFullYear();
      const response = await fetch(`${API_URL}/trend/${userId}?year=${currentYear}`);

      if (response.status === 404) {
        setSummary({
          trend_direction: "insufficient_data",
          trend_summary: "Not enough data for this year yet!",
          scores_analyzed: 0
        });
        return;
      }

      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const data = await response.json();
      setSummary(data);

    } catch (err) {
      console.error('Error fetching year summary:', err);
    } finally {
      setSummaryLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={COLORS.amber} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  if (scores.length === 0) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyText}>No data available for the graph</Text>
      </View>
    );
  }

  // Calculate dynamic width: each day gets 60px of space
  const screenWidth = Dimensions.get('window').width;
  // Account for Y-axis and card padding
  const availableWidth = screenWidth - (SPACING.md * 2) - Y_AXIS_WIDTH;
  const chartWidth = Math.max(availableWidth, scores.length * 60);

  const chartConfig = {
    backgroundColor: COLORS.card,
    backgroundGradientFrom: COLORS.card,
    backgroundGradientTo: COLORS.card,
    decimalPlaces: 0,
    color: (opacity = 1) => COLORS.border,
    labelColor: (opacity = 1) => COLORS.textSecondary,
    style: {
      borderRadius: RADIUS.lg
    },
    propsForDots: {
      r: "5",
      strokeWidth: "2",
      stroke: COLORS.card
    },
    propsForLabels: {
      fontSize: 10,
      fontWeight: FONTS.weights.medium
    },
  };

  // Map data for react-native-chart-kit
  const chartData = {
    labels: scores.map(s => s.date),
    datasets: [
      {
        data: scores.map(s => s.vibe_score),
        color: () => COLORS.amber,
      },
      {
        data: new Array(scores.length).fill(100), // Force 0-100 range scale
        withDots: false,
        color: () => 'transparent',
      }
    ]
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Vibe Trend</Text>

      <View style={styles.chartWrapper}>
        {/* Fixed Y-Axis Container */}
        <View style={styles.yAxisContainer}>
          <LineChart
            data={{
              labels: [],
              datasets: [{ data: [0, 100], color: () => 'transparent' }]
            }}
            width={screenWidth} // Will be clipped by container
            height={CHART_HEIGHT}
            chartConfig={chartConfig}
            fromZero
            segments={5}
            withDots={false}
            withVerticalLabels={false}
            style={styles.yAxisChart}
          />
        </View>

        {/* Scrollable Chart Content */}
        <ScrollView 
          horizontal 
          ref={scrollViewRef}
          showsHorizontalScrollIndicator={Platform.OS === 'web'}
          style={styles.scrollContainer}
          contentContainerStyle={{ 
            paddingRight: SPACING.md,
            minWidth: '100%' 
          }}
        >
          <LineChart
            data={chartData}
            width={chartWidth}
            height={CHART_HEIGHT}
            yAxisInterval={1}
            fromZero={true}
            segments={5}
            withHorizontalLabels={false}
            chartConfig={chartConfig}
            bezier
            style={styles.mainChart}
            verticalLabelRotation={30}
            getDotColor={(dataPoint) => getVibeColor(dataPoint)}
          />
        </ScrollView>
      </View>

      <TouchableOpacity
        style={styles.summaryButton}
        onPress={fetchYearSummary}
        disabled={summaryLoading}
        activeOpacity={0.7}
      >
        {summaryLoading ? (
          <ActivityIndicator size="small" color={COLORS.white} />
        ) : (
          <View style={styles.buttonContent}>
            <Ionicons name="calendar-outline" size={16} color={COLORS.white} />
            <Text style={styles.summaryButtonText}>Year Summary</Text>
          </View>
        )}
      </TouchableOpacity>

      {summary && (
        <View style={styles.summaryCard}>
          <View style={styles.summaryHeader}>
            <Text style={styles.summaryTitle}>Annual Outlook</Text>
            {summary.trend_direction !== 'insufficient_data' && (
              <View style={[
                styles.badge,
                {
                  backgroundColor: getTrendColor(summary.trend_direction) + '20',
                  borderColor: getTrendColor(summary.trend_direction)
                }
              ]}>
                <Text style={[styles.badgeText, { color: getTrendColor(summary.trend_direction) }]}>
                  {summary.trend_direction}
                </Text>
              </View>
            )}
          </View>
          <Text style={styles.summaryText}>{summary.trend_summary}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.card,
    borderRadius: RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  chartWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    width: '100%',
    overflow: 'hidden',
  },
  yAxisContainer: {
    width: Y_AXIS_WIDTH,
    overflow: 'hidden',
    zIndex: 1,
    backgroundColor: COLORS.card,
  },
  yAxisChart: {
    marginLeft: -15,
  },
  scrollContainer: {
    flex: 1,
  },
  mainChart: {
    marginVertical: 8,
    borderRadius: RADIUS.lg,
    marginLeft: -10, // Slight overlap to align grid lines perfectly
  },
  title: {
    color: COLORS.textSecondary,
    fontSize: FONTS.sizes.xs,
    fontWeight: FONTS.weights.bold,
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    marginBottom: SPACING.md,
  },
  center: {
    height: 220,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: RADIUS.lg,
    marginBottom: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  errorText: {
    color: COLORS.error,
    fontSize: FONTS.sizes.sm,
  },
  emptyText: {
    color: COLORS.textSecondary,
    fontSize: FONTS.sizes.sm,
  },
  summaryButton: {
    backgroundColor: COLORS.amber,
    borderRadius: RADIUS.md,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: SPACING.md,
    height: 40,
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  summaryButtonText: {
    color: COLORS.white,
    fontSize: FONTS.sizes.sm,
    fontWeight: FONTS.weights.bold,
  },
  summaryCard: {
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.md,
    padding: SPACING.md,
    marginTop: SPACING.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  summaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  summaryTitle: {
    color: COLORS.amber,
    fontSize: FONTS.sizes.xs,
    fontWeight: FONTS.weights.bold,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  summaryText: {
    color: COLORS.textPrimary,
    fontSize: FONTS.sizes.sm,
    lineHeight: 20,
  },
  badge: {
    paddingHorizontal: SPACING.sm,
    paddingVertical: 2,
    borderRadius: RADIUS.full,
    borderWidth: 1,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: FONTS.weights.bold,
    textTransform: 'uppercase',
  },
});