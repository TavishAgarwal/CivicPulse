import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/firestore_service.dart';

class HomeScreen extends StatelessWidget {
  final FirestoreService _fs = FirestoreService();

  HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                  Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: AppTheme.accent,
                      boxShadow: [
                        BoxShadow(
                          color: AppTheme.accent.withValues(alpha: 0.5),
                          blurRadius: 8,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 10),
                  Text('CivicPulse',
                      style: Theme.of(context).textTheme.headlineMedium),
                  const Spacer(),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.accent.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppTheme.accent, width: 1),
                    ),
                    child: Text('VOLUNTEER',
                        style: Theme.of(context)
                            .textTheme
                            .bodyMedium
                            ?.copyWith(
                                color: AppTheme.accent,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 1.5)),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Pulse Overview
              Text('LIVE WARD STATUS',
                  style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 12),

              // Ward list from Firestore
              StreamBuilder<List<Map<String, dynamic>>>(
                stream: _fs.watchWards(),
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Center(
                      child: Padding(
                        padding: EdgeInsets.all(40),
                        child: CircularProgressIndicator(
                            color: AppTheme.accent),
                      ),
                    );
                  }

                  if (snapshot.hasError) {
                    return _buildErrorCard(
                        'Failed to load wards: ${snapshot.error}');
                  }

                  final wards = snapshot.data ?? [];
                  if (wards.isEmpty) {
                    return _buildErrorCard('No ward data available.');
                  }

                  // Summary cards
                  final critical = wards
                      .where((w) => (w['css'] as num? ?? 0) >= 76)
                      .length;
                  final high = wards
                      .where((w) {
                        final css = (w['css'] as num? ?? 0).toDouble();
                        return css >= 56 && css < 76;
                      })
                      .length;
                  final avgCss = wards.fold<double>(
                          0, (sum, w) => sum + (w['css'] as num? ?? 0)) /
                      wards.length;

                  return Column(
                    children: [
                      // Summary row
                      Row(
                        children: [
                          _SummaryChip(
                            icon: Icons.warning_rounded,
                            label: 'Critical',
                            value: '$critical',
                            color: AppTheme.critical,
                          ),
                          const SizedBox(width: 8),
                          _SummaryChip(
                            icon: Icons.trending_up,
                            label: 'High',
                            value: '$high',
                            color: AppTheme.high,
                          ),
                          const SizedBox(width: 8),
                          _SummaryChip(
                            icon: Icons.analytics_outlined,
                            label: 'Avg CSS',
                            value: avgCss.toStringAsFixed(1),
                            color: AppTheme.cssColor(avgCss),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),

                      // Ward cards
                      ...wards.take(15).map((ward) => _WardCard(ward: ward)),
                    ],
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildErrorCard(String message) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            const Icon(Icons.error_outline, color: AppTheme.critical),
            const SizedBox(width: 12),
            Expanded(
              child: Text(message,
                  style: const TextStyle(color: AppTheme.textSecondary)),
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _SummaryChip({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 18),
            const SizedBox(height: 6),
            Text(value,
                style: TextStyle(
                  color: color,
                  fontSize: 22,
                  fontWeight: FontWeight.w700,
                )),
            Text(label,
                style: const TextStyle(
                  color: AppTheme.textMuted,
                  fontSize: 10,
                  letterSpacing: 1,
                )),
          ],
        ),
      ),
    );
  }
}

class _WardCard extends StatelessWidget {
  final Map<String, dynamic> ward;

  const _WardCard({required this.ward});

  @override
  Widget build(BuildContext context) {
    final css = (ward['css'] as num? ?? 0).toDouble();
    final name = ward['name'] as String? ?? ward['id'];
    final wardId = ward['id'] as String? ?? '';
    final color = AppTheme.cssColor(css);
    final label = AppTheme.cssLabel(css);

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () {
            Navigator.pushNamed(context, '/ward', arguments: wardId);
          },
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: color.withValues(alpha: 0.25),
              ),
            ),
            child: Row(
              children: [
                // CSS score circle
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: color.withValues(alpha: 0.15),
                    border: Border.all(color: color, width: 2),
                  ),
                  alignment: Alignment.center,
                  child: Text(
                    css.toStringAsFixed(0),
                    style: TextStyle(
                      color: color,
                      fontWeight: FontWeight.w700,
                      fontSize: 16,
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                // Ward info
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        name,
                        style: const TextStyle(
                          color: AppTheme.textPrimary,
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        wardId,
                        style: const TextStyle(
                          color: AppTheme.textMuted,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                // Status badge
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    label.toUpperCase(),
                    style: TextStyle(
                      color: color,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Icon(Icons.chevron_right, color: color.withValues(alpha: 0.5)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
