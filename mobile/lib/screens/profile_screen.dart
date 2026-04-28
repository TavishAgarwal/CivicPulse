import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/firestore_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final FirestoreService _fs = FirestoreService();
  String _selectedVolunteerId = 'vol_000';
  Map<String, dynamic>? _profile;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    setState(() => _loading = true);
    final profile =
        await _fs.getVolunteerProfile(_selectedVolunteerId);
    if (mounted) {
      setState(() {
        _profile = profile;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Profile',
                  style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 4),
              Text('Volunteer dashboard',
                  style: Theme.of(context).textTheme.bodyMedium),
              const SizedBox(height: 20),

              // Volunteer selector (demo)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.surface,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.border),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('DEMO VOLUNTEER',
                        style: TextStyle(
                          color: AppTheme.textMuted,
                          fontSize: 10,
                          letterSpacing: 1.5,
                        )),
                    const SizedBox(height: 8),
                    DropdownButton<String>(
                      value: _selectedVolunteerId,
                      isExpanded: true,
                      dropdownColor: AppTheme.surface,
                      style: const TextStyle(
                          color: AppTheme.textPrimary, fontSize: 14),
                      items: List.generate(10, (i) {
                        final id = 'vol_${i.toString().padLeft(3, '0')}';
                        return DropdownMenuItem(value: id, child: Text(id));
                      }),
                      onChanged: (v) {
                        if (v != null) {
                          _selectedVolunteerId = v;
                          _loadProfile();
                        }
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              if (_loading)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(40),
                    child:
                        CircularProgressIndicator(color: AppTheme.accent),
                  ),
                )
              else if (_profile == null)
                const Center(
                  child: Text('Profile not found',
                      style: TextStyle(color: AppTheme.textSecondary)),
                )
              else
                _buildProfile(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProfile() {
    final name = _profile!['handle'] as String? ?? _selectedVolunteerId;
    final skills = List<String>.from(_profile!['skills'] ?? []);
    final fatigue = (_profile!['fatigue_score'] as num? ?? 0).toDouble();
    final rating = (_profile!['performance_rating'] as num? ?? 0).toDouble();
    final maxRadius = (_profile!['max_radius_km'] as num? ?? 10).toInt();
    final status = _profile!['status'] as String? ?? 'available';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Avatar + Name
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: AppTheme.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppTheme.border),
          ),
          child: Column(
            children: [
              CircleAvatar(
                radius: 36,
                backgroundColor: AppTheme.accent.withValues(alpha: 0.15),
                child: Text(
                  name.isNotEmpty ? name[0].toUpperCase() : 'V',
                  style: const TextStyle(
                    color: AppTheme.accent,
                    fontSize: 28,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Text(name,
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                  )),
              const SizedBox(height: 6),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: status == 'available'
                      ? AppTheme.accent.withValues(alpha: 0.15)
                      : AppTheme.elevated.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  status.toUpperCase(),
                  style: TextStyle(
                    color: status == 'available'
                        ? AppTheme.accent
                        : AppTheme.elevated,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.5,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // Stats row
        Row(
          children: [
            _StatCard(
              icon: Icons.star,
              label: 'Rating',
              value: rating.toStringAsFixed(1),
              color: AppTheme.accent,
            ),
            const SizedBox(width: 8),
            _StatCard(
              icon: Icons.battery_4_bar,
              label: 'Fatigue',
              value: '${(fatigue * 100).toStringAsFixed(0)}%',
              color: fatigue > 0.7
                  ? AppTheme.critical
                  : fatigue > 0.4
                      ? AppTheme.elevated
                      : AppTheme.stable,
            ),
            const SizedBox(width: 8),
            _StatCard(
              icon: Icons.radar,
              label: 'Radius',
              value: '${maxRadius}km',
              color: AppTheme.textSecondary,
            ),
          ],
        ),
        const SizedBox(height: 16),

        // Skills
        Text('SKILLS',
            style: Theme.of(context).textTheme.labelLarge),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: skills.map((skill) {
            return Container(
              padding: const EdgeInsets.symmetric(
                  horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: AppTheme.surfaceLight,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppTheme.border),
              ),
              child: Text(
                skill.toUpperCase(),
                style: const TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1,
                ),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 24),

        // Notification settings
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppTheme.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppTheme.border),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('NOTIFICATIONS',
                  style: TextStyle(
                    color: AppTheme.textMuted,
                    fontSize: 10,
                    letterSpacing: 1.5,
                  )),
              const SizedBox(height: 12),
              _SettingsRow(
                icon: Icons.notifications_active,
                label: 'Dispatch Alerts',
                value: true,
              ),
              _SettingsRow(
                icon: Icons.warning,
                label: 'Critical Ward Alerts',
                value: true,
              ),
              _SettingsRow(
                icon: Icons.summarize,
                label: 'Weekly Summary',
                value: false,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _StatCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.border),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(height: 6),
            Text(value,
                style: TextStyle(
                  color: color,
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                )),
            Text(label,
                style: const TextStyle(
                  color: AppTheme.textMuted,
                  fontSize: 10,
                )),
          ],
        ),
      ),
    );
  }
}

class _SettingsRow extends StatefulWidget {
  final IconData icon;
  final String label;
  final bool value;

  const _SettingsRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  State<_SettingsRow> createState() => _SettingsRowState();
}

class _SettingsRowState extends State<_SettingsRow> {
  late bool _enabled;

  @override
  void initState() {
    super.initState();
    _enabled = widget.value;
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(widget.icon, color: AppTheme.textSecondary, size: 18),
          const SizedBox(width: 12),
          Expanded(
            child: Text(widget.label,
                style: const TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 13,
                )),
          ),
          Switch(
            value: _enabled,
            activeTrackColor: AppTheme.accent.withValues(alpha: 0.4),
            thumbColor: WidgetStatePropertyAll(_enabled ? AppTheme.accent : AppTheme.textMuted),
            onChanged: (v) => setState(() => _enabled = v),
          ),
        ],
      ),
    );
  }
}
