import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/firestore_service.dart';

class DispatchesScreen extends StatelessWidget {
  final FirestoreService _fs = FirestoreService();

  DispatchesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Dispatch Feed',
                      style: Theme.of(context).textTheme.headlineMedium),
                  const SizedBox(height: 4),
                  Text('Real-time volunteer dispatch assignments',
                      style: Theme.of(context).textTheme.bodyMedium),
                ],
              ),
            ),

            // Dispatch list
            Expanded(
              child: StreamBuilder<List<Map<String, dynamic>>>(
                stream: _fs.watchDispatches(),
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Center(
                      child:
                          CircularProgressIndicator(color: AppTheme.accent),
                    );
                  }

                  if (snapshot.hasError) {
                    return Center(
                      child: Text('Error: ${snapshot.error}',
                          style: const TextStyle(color: AppTheme.critical)),
                    );
                  }

                  final dispatches = snapshot.data ?? [];
                  if (dispatches.isEmpty) {
                    return Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.check_circle_outline,
                              size: 64,
                              color: AppTheme.accent.withValues(alpha: 0.3)),
                          const SizedBox(height: 16),
                          const Text('No active dispatches',
                              style:
                                  TextStyle(color: AppTheme.textSecondary)),
                        ],
                      ),
                    );
                  }

                  return ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: dispatches.length,
                    itemBuilder: (context, index) =>
                        _DispatchCard(dispatch: dispatches[index], fs: _fs),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DispatchCard extends StatelessWidget {
  final Map<String, dynamic> dispatch;
  final FirestoreService fs;

  const _DispatchCard({required this.dispatch, required this.fs});

  Color _statusColor(String status) {
    switch (status.toLowerCase()) {
      case 'active':
        return AppTheme.accent;
      case 'confirmed':
        return AppTheme.elevated;
      case 'completed':
        return AppTheme.stable;
      case 'cancelled':
        return AppTheme.critical;
      default:
        return AppTheme.textMuted;
    }
  }

  IconData _statusIcon(String status) {
    switch (status.toLowerCase()) {
      case 'active':
        return Icons.flash_on;
      case 'confirmed':
        return Icons.thumb_up;
      case 'completed':
        return Icons.check_circle;
      case 'cancelled':
        return Icons.cancel;
      default:
        return Icons.radio_button_unchecked;
    }
  }

  @override
  Widget build(BuildContext context) {
    final status = dispatch['status'] as String? ?? 'pending';
    final wardId = dispatch['wardId'] as String? ?? '—';
    final volunteer = dispatch['volunteerName'] as String? ?? '—';
    final reason = dispatch['reason'] as String? ?? '';
    final color = _statusColor(status);
    final dispatchId = dispatch['id'] as String? ?? '';

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.25)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header row
            Row(
              children: [
                Icon(_statusIcon(status), color: color, size: 18),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(wardId,
                      style: const TextStyle(
                        color: AppTheme.textPrimary,
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      )),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    status.toUpperCase(),
                    style: TextStyle(
                      color: color,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            // Volunteer
            Row(
              children: [
                const Icon(Icons.person, color: AppTheme.textMuted, size: 14),
                const SizedBox(width: 6),
                Text(volunteer,
                    style: const TextStyle(
                      color: AppTheme.textSecondary,
                      fontSize: 12,
                    )),
              ],
            ),
            if (reason.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(reason,
                  style: const TextStyle(
                    color: AppTheme.textMuted,
                    fontSize: 11,
                  )),
            ],
            // Action buttons for active dispatches
            if (status.toLowerCase() == 'active' ||
                status.toLowerCase() == 'confirmed') ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  if (status.toLowerCase() == 'active')
                    Expanded(
                      child: OutlinedButton.icon(
                        icon: const Icon(Icons.check, size: 16),
                        label: const Text('ACCEPT'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppTheme.accent,
                          side: const BorderSide(color: AppTheme.accent),
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          textStyle: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1,
                          ),
                        ),
                        onPressed: () {
                          fs.updateDispatchStatus(dispatchId, 'confirmed');
                        },
                      ),
                    ),
                  if (status.toLowerCase() == 'active')
                    const SizedBox(width: 8),
                  if (status.toLowerCase() == 'confirmed')
                    Expanded(
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.check_circle, size: 16),
                        label: const Text('COMPLETE'),
                        onPressed: () {
                          fs.updateDispatchStatus(dispatchId, 'completed');
                        },
                      ),
                    ),
                  if (status.toLowerCase() != 'completed')
                    const SizedBox(width: 8),
                  if (status.toLowerCase() != 'completed')
                    SizedBox(
                      width: 90,
                      child: OutlinedButton(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppTheme.critical,
                          side: const BorderSide(color: AppTheme.critical),
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          textStyle: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        onPressed: () {
                          fs.updateDispatchStatus(dispatchId, 'cancelled');
                        },
                        child: const Text('DECLINE'),
                      ),
                    ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
