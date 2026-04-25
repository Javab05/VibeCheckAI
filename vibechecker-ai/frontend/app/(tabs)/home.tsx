import { View, Text, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { COLORS, SPACING, RADIUS, FONTS } from '../../constants/theme';

const { width } = Dimensions.get('window');
const CARD_WIDTH = width - SPACING.xl * 2;

export default function DashboardScreen() {
    return (
        <SafeAreaView style={styles.safe}>
            <View style={styles.header}>
                <Text style={styles.sectionLabel}>Dashboard</Text>
                <Text style={styles.title}>Your mood hub</Text>
                <Text style={styles.subtitle}>
                    Choose the next action and keep your seasonal check-ins on track.
                </Text>
            </View>

            <View style={styles.body}>
                <TouchableOpacity
                    activeOpacity={0.88}
                    style={styles.card}
                    onPress={() => router.navigate('/scan')}
                >
                    <LinearGradient
                        colors={[COLORS.amber, COLORS.coral]}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 1 }}
                        style={styles.cardIcon}
                    >
                        <Ionicons name="camera" size={24} color={COLORS.white} />
                    </LinearGradient>
                    <Text style={styles.cardTitle}>Daily Check-in</Text>
                    <Text style={styles.cardText}>Snap a selfie and get a quick mood evaluation.</Text>
                </TouchableOpacity>

                <TouchableOpacity
                    activeOpacity={0.88}
                    style={styles.card}
                    onPress={() => router.navigate('/history')}
                >
                    <View style={[styles.cardIcon, styles.cardIconSecondary]}>
                        <Ionicons name="time" size={24} color={COLORS.white} />
                    </View>
                    <Text style={styles.cardTitle}>Mood History</Text>
                    <Text style={styles.cardText}>Review past scans and seasonal progress.</Text>
                </TouchableOpacity>
            </View>

            <View style={styles.footer}>
                <Text style={styles.footerTitle}>Tip</Text>
                <Text style={styles.footerText}>
                    Regular check-ins help the app learn your seasonal mood patterns faster.
                </Text>
            </View>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safe: { flex: 1, backgroundColor: COLORS.background, paddingHorizontal: SPACING.xl },
    header: { paddingTop: SPACING['2xl'], paddingBottom: SPACING.lg },
    sectionLabel: {
        color: COLORS.amber, fontSize: FONTS.sizes.xs,
        fontWeight: FONTS.weights.bold, letterSpacing: 1.5,
        textTransform: 'uppercase', marginBottom: SPACING.sm,
    },
    title: {
        color: COLORS.textPrimary, fontSize: FONTS.sizes['4xl'],
        fontWeight: FONTS.weights.black, lineHeight: 48,
        marginBottom: SPACING.sm,
    },
    subtitle: {
        color: COLORS.textSecondary, fontSize: FONTS.sizes.md,
        lineHeight: 24, maxWidth: '88%',
    },
    body: { gap: SPACING.lg, paddingTop: SPACING.lg },
    card: {
        width: CARD_WIDTH,
        backgroundColor: COLORS.card,
        borderRadius: RADIUS.xl,
        borderWidth: 1,
        borderColor: COLORS.border,
        padding: SPACING.xl,
        shadowColor: '#000',
        shadowOpacity: 0.05,
        shadowRadius: 20,
        elevation: 4,
    },
    cardIcon: {
        width: 56,
        height: 56,
        borderRadius: RADIUS.full,
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: SPACING.md,
    },
    cardIconSecondary: {
        backgroundColor: COLORS.steelDeep,
    },
    cardTitle: {
        color: COLORS.textPrimary,
        fontSize: FONTS.sizes['2xl'],
        fontWeight: FONTS.weights.bold,
        marginBottom: SPACING.xs,
    },
    cardText: {
        color: COLORS.textSecondary,
        fontSize: FONTS.sizes.md,
        lineHeight: 22,
    },
    footer: { marginTop: SPACING['2xl'], paddingBottom: SPACING['2xl'] },
    footerTitle: {
        color: COLORS.amber,
        fontSize: FONTS.sizes.xs,
        fontWeight: FONTS.weights.bold,
        letterSpacing: 1.5,
        textTransform: 'uppercase',
        marginBottom: SPACING.xs,
    },
    footerText: {
        color: COLORS.textSecondary,
        fontSize: FONTS.sizes.sm,
        lineHeight: 20,
    },
});
