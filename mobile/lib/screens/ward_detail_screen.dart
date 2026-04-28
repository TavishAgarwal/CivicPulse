import 'package:flutter/material.dart';
import '../theme.dart';
import '../services/firestore_service.dart';

class WardDetailScreen extends StatefulWidget {
  final String wardId;

  const WardDetailScreen({super.key, required this.wardId});

  @override
  State<WardDetailScreen> createState() => _WardDetailScreenState();
}

class _WardDetailScreenState extends State<WardDetailScreen> {
  final FirestoreService _fs = FirestoreService();
  Map<String, dynamic>? _ward;
  List<Map<String, dynamic>> _history = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final ward = await _fs.getWard(widget.wardId);
    final history = await _fs.getWardCSSHistory(widget.wardId);
    if (mounted) {
      setState(() {
        _ward = ward;
        _history = history.reversed.toList();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: Text(widget.wardId)),
        body: const Center(
          child: CircularProgressIndicator(color: AppTheme.accent),
        ),
      );
    }

    if (_ward == null) {
      return Scaffold(
        appBar: AppBar(title: Text(widget.wardId)),
        body: const Center(
          child: Text('Ward not found', style: TextStyle(color: AppTheme.textSecondary)),
        ),
      );
    }

    final css = (_ward!['css'] as num? ?? 0).toDouble();
    final name = _ward!['name'] as String? ?? widget.wardId;
    final color = AppTheme.cssColor(css);
    final label = AppTheme.cssLabel(css);
    final signals = _ward!['signals'] as Map<String, dynamic>? ?? {};

    return Scaffold(
      appBar: AppBar(
        title: Text(name),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // CSS score hero
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    color.withValues(alpha: 0.15),
                    AppTheme.surface,
                  ],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: color.withValues(alpha: 0.3)),
              ),
              child: Column(
                children: [
                  Text('Community Stress Score',
                      style: TextStyle(
                        color: color.withValues(alpha: 0.7),
                        fontSize: 12,
                        letterSpacing: 2,
                        fontWeight: FontWeight.w600,
                      )),
                  const SizedBox(height: 12),
                  Text(
                    css.toStringAsFixed(1),
                    style: TextStyle(
                      color: color,
                      fontSize: 56,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 6),
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      label.toUpperCase(),
                      style: TextStyle(
                        color: color,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 2,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(widget.wardId,
                      style: const TextStyle(
                        color: AppTheme.textMuted,
                        fontSize: 11,
                      )),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Signal breakdown
            if (signals.isNotEmpty) ...[
              Text('SIGNAL BREAKDOWN',
                  style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 12),
              ...signals.entries.map((e) => _SignalBar(
                    label: _formatSignalName(e.key),
                    value: (e.value as num? ?? 0).toDouble(),
                  )),
              const SizedBox(height: 20),
            ],

            // CSS History
            if (_history.isNotEmpty) ...[
              Text('14-DAY TREND',
                  style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 12),
              SizedBox(
                height: 120,
                child: _CSSMiniChart(history: _history),
              ),
              const SizedBox(height: 20),
            ],

            // Auto dispatch info
            if (css >= 76)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.critical.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                      color: AppTheme.critical.withValues(alpha: 0.3)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.warning_amber, color: AppTheme.critical),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Auto-dispatch eligible\nCSS ≥ 76 — volunteers can be auto-dispatched',
                        style: TextStyle(
                          color: AppTheme.critical,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  String _formatSignalName(String key) {
    return key
        .replaceAll('_', ' ')
        .split(' ')
        .map((w) => w.isNotEmpty
            ? '${w[0].toUpperCase()}${w.substring(1)}'
            : '')
        .join(' ');
  }
}

class _SignalBar extends StatelessWidget {
  final String label;
  final double value;

  const _SignalBar({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final clampedValue = value.clamp(0.0, 1.0);
    final color = AppTheme.cssColor(clampedValue * 100);

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label,
                  style: const TextStyle(
                      color: AppTheme.textSecondary, fontSize: 11)),
              Text('${(clampedValue * 100).toStringAsFixed(0)}%',
                  style: TextStyle(color: color, fontSize: 11)),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: clampedValue,
              backgroundColor: AppTheme.surfaceLight,
              valueColor: AlwaysStoppedAnimation(color),
              minHeight: 6,
            ),
          ),
        ],
      ),
    );
  }
}

class _CSSMiniChart extends StatelessWidget {
  final List<Map<String, dynamic>> history;

  const _CSSMiniChart({required this.history});

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: _ChartPainter(history),
      size: Size.infinite,
    );
  }
}

class _ChartPainter extends CustomPainter {
  final List<Map<String, dynamic>> history;

  _ChartPainter(this.history);

  @override
  void paint(Canvas canvas, Size size) {
    if (history.isEmpty) return;

    final paint = Paint()
      ..color = AppTheme.accent
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    final fillPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [
          AppTheme.accent.withValues(alpha: 0.3),
          AppTheme.accent.withValues(alpha: 0.0),
        ],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));

    final path = Path();
    final fillPath = Path();

    final maxCss = 100.0;
    final stepX = size.width / (history.length - 1).clamp(1, 999);

    for (var i = 0; i < history.length; i++) {
      final css = (history[i]['css'] as num? ?? 0).toDouble();
      final x = i * stepX;
      final y = size.height - (css / maxCss * size.height);

      if (i == 0) {
        path.moveTo(x, y);
        fillPath.moveTo(x, size.height);
        fillPath.lineTo(x, y);
      } else {
        path.lineTo(x, y);
        fillPath.lineTo(x, y);
      }
    }

    fillPath.lineTo(size.width, size.height);
    fillPath.close();

    canvas.drawPath(fillPath, fillPaint);
    canvas.drawPath(path, paint);

    // Draw dots
    final dotPaint = Paint()..style = PaintingStyle.fill;
    for (var i = 0; i < history.length; i++) {
      final css = (history[i]['css'] as num? ?? 0).toDouble();
      final x = i * stepX;
      final y = size.height - (css / maxCss * size.height);
      dotPaint.color = AppTheme.cssColor(css);
      canvas.drawCircle(Offset(x, y), 3, dotPaint);
    }

    // Draw threshold lines
    final thresholdPaint = Paint()
      ..strokeWidth = 0.5
      ..style = PaintingStyle.stroke;

    for (final threshold in [30.0, 55.0, 75.0]) {
      final y = size.height - (threshold / maxCss * size.height);
      thresholdPaint.color = AppTheme.textMuted.withValues(alpha: 0.3);
      canvas.drawLine(Offset(0, y), Offset(size.width, y), thresholdPaint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
