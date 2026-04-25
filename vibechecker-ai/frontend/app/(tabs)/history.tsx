import { View, Text, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { COLORS, SPACING, RADIUS, FONTS } from '../../constants/theme';

const { width } = Dimensions.get('window');
const CARD_WIDTH = width - SPACING.xl * 2;

export default function HistoryPlaceholderScreen() {
    return (
        <SafeAreaView style={styles.safe}>
            <View style={styles.header}>
                <Text style={styles.label}>Mood History</Text>
                <Text style={styles.title}>Coming soon</Text>
                <Text style={styles.subtitle}>
                    We’re preparing your mood timeline and seasonal insight cards. Check back after a few scans.
                </Text>
            </View>

            <View style={styles.card}>
                <Ionicons name="time" size={34} color={COLORS.amber} />
                <Text style={styles.cardTitle}>History is on the way</Text>
                <Text style={styles.cardText}>
                    This screen will show your past check-ins, trends, and emotional snapshots.
                </Text>
            </View>

            <TouchableOpacity activeOpacity={0.85} onPress={() => router.navigate('/home')}>
                <LinearGradient
                    colors={[COLORS.amber, COLORS.coral]}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                    style={styles.button}
                >
                    <Ionicons name="arrow-back" size={18} color={COLORS.white} />
                    <Text style={styles.buttonText}>Back to Dashboard</Text>
                </LinearGradient>
            </TouchableOpacity>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safe: { flex: 1, backgroundColor: COLORS.background, paddingHorizontal: SPACING.xl, paddingTop: SPACING['2xl'], paddingBottom: SPACING.lg },
    header: { marginBottom: SPACING['2xl'] },
    label: {
        color: COLORS.amber,
        fontSize: FONTS.sizes.xs,
        fontWeight: FONTS.weights.bold,
        letterSpacing: 1.5,
        textTransform: 'uppercase',
        marginBottom: SPACING.sm,
    },
    title: {
        color: COLORS.textPrimary,
        fontSize: FONTS.sizes['3xl'],
        fontWeight: FONTS.weights.black,
        marginBottom: SPACING.sm,
    },
    subtitle: {
        color: COLORS.textSecondary,
        fontSize: FONTS.sizes.md,
        lineHeight: 24,
    },
    card: {
        width: CARD_WIDTH,
        flex: 1,
        backgroundColor: COLORS.card,
        borderRadius: RADIUS.xl,
        borderWidth: 1,
        borderColor: COLORS.border,
        padding: SPACING['2xl'],
        justifyContent: 'center',
        alignItems: 'center',
        gap: SPACING.sm,
        marginBottom: SPACING['2xl'],
    },
    cardTitle: {
        color: COLORS.textPrimary,
        fontSize: FONTS.sizes['2xl'],
        fontWeight: FONTS.weights.bold,
        marginTop: SPACING.md,
        textAlign: 'center',
    },
    cardText: {
        color: COLORS.textSecondary,
        fontSize: FONTS.sizes.md,
        lineHeight: 22,
        textAlign: 'center',
        marginTop: SPACING.sm,
    },
    button: {
        borderRadius: RADIUS.full,
        paddingVertical: SPACING.base + 2,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: SPACING.sm,
    },
    buttonText: {
        color: COLORS.white,
        fontWeight: FONTS.weights.bold,
        fontSize: FONTS.sizes.base,
    },
});
