import React, { useState, useEffect } from 'react';
import { View, Text, ActivityIndicator, StyleSheet, Dimensions, TouchableOpacity } from 'react-native';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine,
  Cell
} from 'recharts';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../../constants/api';
import { COLORS, SPACING, RADIUS, FONTS } from '../../constants/theme';

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <View style={styles.tooltip}>
        <Text style={styles.tooltipDate}>{data.date}</Text>
        <Text style={[styles.tooltipScore, { color: getVibeColor(data.vibe_score) }]}>
          Vibe: {data.vibe_score}
        </Text>
        <Text style={styles.tooltipEmotion}>{data.dominant_emotion}</Text>
      </View>
    );
  }
  return null;
};

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

  useEffect(() => {
    if (!initialScores) {
      fetchScores();
    } else {
      setScores(initialScores);
    }
  }, [initialScores]);

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
      // console.log('Raw History API Response:', JSON.stringify(data, null, 2));
      
      // Transform backend data to graph format
      const transformedData = data.map(item => {
        // Map vibe_score from scores object. 
        // Note: New data will have vibe_score inside item.scores
        // Fallback to calculation for old data where it might be missing
        let vibeScore = item.scores?.vibe_score;
        
        if (vibeScore === undefined || vibeScore === null) {
            // Fallback: (happy - sad) * 50 + 50
            const happy = item.scores?.happy ?? 0;
            const sad = item.scores?.sad ?? 0;
            vibeScore = Math.round((happy - sad) * 50 + 50);
        }

        return {
          date: new Date(item.captured_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          vibe_score: vibeScore,
          dominant_emotion: item.emotion || 'neutral'
        };
      }); // Oldest to newest for graph

      setScores(transformedData.slice(-30));
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
      
      // 1. Catch the 404 (No Data)
      if (response.status === 404) {
        setSummary({
          trend_direction: "insufficient_data",
          trend_summary: "Not enough data for this year yet!",
          scores_analyzed: 0
        });
        
        return; // Exit the function successfully
      }

      // 2. Catch actual server crashes (500s)
      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      
      // 3. Otherwise success
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

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Vibe Trend</Text>
      <View style={{ width: '100%', height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={scores} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.divider} vertical={false} />
            <XAxis 
              dataKey="date" 
              stroke={COLORS.textMuted} 
              fontSize={10}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              domain={[0, 100]} 
              stroke={COLORS.textMuted} 
              fontSize={10}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: COLORS.border }} />
            <ReferenceLine y={50} stroke={COLORS.textMuted} strokeDasharray="3 3" />
            <Line
              type="monotone"
              dataKey="vibe_score"
              stroke={COLORS.amber}
              strokeWidth={3}
              dot={(props) => {
                const { cx, cy, payload } = props;
                return (
                  <circle 
                    cx={cx} 
                    cy={cy} 
                    r={4} 
                    fill={getVibeColor(payload.vibe_score)} 
                    stroke={COLORS.card}
                    strokeWidth={2}
                  />
                );
              }}
              activeDot={{ r: 6, strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
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
  tooltip: {
    backgroundColor: COLORS.surface,
    padding: SPACING.sm,
    borderRadius: RADIUS.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  tooltipDate: {
    color: COLORS.textMuted,
    fontSize: 10,
    marginBottom: 2,
  },
  tooltipScore: {
    fontSize: FONTS.sizes.md,
    fontWeight: FONTS.weights.bold,
  },
  tooltipEmotion: {
    color: COLORS.textSecondary,
    fontSize: 10,
    textTransform: 'capitalize',
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
