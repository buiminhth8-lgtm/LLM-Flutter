import 'package:flutter/material.dart';

import '../models/evaluation_finding_dto.dart';
import 'evaluation_finding_detail.dart';

class EvaluationFindingsTable extends StatelessWidget {
  const EvaluationFindingsTable({
    super.key,
    required this.findings,
    required this.onStatusChanged,
  });

  final List<EvaluationFindingDto> findings;
  final void Function(String findingId, String status) onStatusChanged;

  @override
  Widget build(BuildContext context) {
    if (findings.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Text('暂无发现项。机房里安静得很。'),
        ),
      );
    }
    return Card(
      key: const Key('evaluation-findings-table'),
      child: ListView.separated(
        itemCount: findings.length,
        separatorBuilder: (_, _) => const Divider(height: 1),
        itemBuilder: (context, index) {
          final finding = findings[index];
          return ListTile(
            key: Key('evaluation-finding-${finding.findingId}'),
            leading: Icon(
              _icon(finding.severity),
              color: _color(finding.severity),
            ),
            title: Text(finding.title),
            subtitle: Text(
              '${finding.category} · ${finding.message}',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            onTap: () => showDialog<void>(
              context: context,
              builder: (_) => EvaluationFindingDetail(finding: finding),
            ),
            trailing: DropdownButton<String>(
              key: Key('evaluation-finding-status-${finding.findingId}'),
              value: finding.status,
              items: const [
                DropdownMenuItem(value: 'open', child: Text('open')),
                DropdownMenuItem(
                  value: 'acknowledged',
                  child: Text('acknowledged'),
                ),
                DropdownMenuItem(value: 'resolved', child: Text('resolved')),
                DropdownMenuItem(value: 'dismissed', child: Text('dismissed')),
              ],
              onChanged: (value) {
                if (value != null) {
                  onStatusChanged(finding.findingId, value);
                }
              },
            ),
          );
        },
      ),
    );
  }

  static IconData _icon(String severity) => switch (severity) {
    'critical' => Icons.priority_high_outlined,
    'error' => Icons.error_outline,
    'warning' => Icons.warning_amber_outlined,
    _ => Icons.info_outline,
  };

  static Color? _color(String severity) => switch (severity) {
    'critical' || 'error' => Colors.red,
    'warning' => Colors.orange,
    _ => null,
  };
}
