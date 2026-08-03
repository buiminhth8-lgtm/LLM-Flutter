import 'package:flutter/material.dart';

import '../models/adapter_eval_case_dto.dart';

class AdapterEvalCaseList extends StatelessWidget {
  const AdapterEvalCaseList({
    super.key,
    required this.cases,
    required this.onSelect,
  });

  final List<AdapterEvalCaseDto> cases;
  final ValueChanged<String> onSelect;

  @override
  Widget build(BuildContext context) {
    if (cases.isEmpty) {
      return const Text('暂无用例。请先添加用例再运行评估。');
    }
    return Column(
      children: [
        for (final item in cases)
          ListTile(
            key: Key('adapter-eval-case-${item.caseId}'),
            title: Text(item.title),
            subtitle: Text('${item.mode} · ${item.status}'),
                      trailing: Text('${item.results.length} 个结果'),
            onTap: () => onSelect(item.caseId),
          ),
      ],
    );
  }
}
