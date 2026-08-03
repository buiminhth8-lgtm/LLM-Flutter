import 'package:flutter/material.dart';

import '../models/adapter_eval_session_dto.dart';

class AdapterEvalSessionList extends StatelessWidget {
  const AdapterEvalSessionList({
    super.key,
    required this.sessions,
    required this.onSelect,
  });

  final List<AdapterEvalSessionDto> sessions;
  final ValueChanged<String> onSelect;

  @override
  Widget build(BuildContext context) {
    if (sessions.isEmpty) {
      return const Center(child: Text('暂无适配器评估会话。'));
    }
    return ListView.builder(
      itemCount: sessions.length,
      itemBuilder: (context, index) {
        final item = sessions[index];
        return ListTile(
          key: Key('adapter-eval-session-${item.sessionId}'),
          title: Text(item.name),
          subtitle: Text(
            '${item.baseModelId} + ${item.adapterId} · ${item.status}',
          ),
          onTap: () => onSelect(item.sessionId),
        );
      },
    );
  }
}
