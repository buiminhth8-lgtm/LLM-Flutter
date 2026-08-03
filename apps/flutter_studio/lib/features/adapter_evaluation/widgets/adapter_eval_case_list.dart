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
      return const Text('No cases. Add a case before running evaluation.');
    }
    return Column(
      children: [
        for (final item in cases)
          ListTile(
            key: Key('adapter-eval-case-${item.caseId}'),
            title: Text(item.title),
            subtitle: Text('${item.mode} · ${item.status}'),
            trailing: Text('${item.results.length} results'),
            onTap: () => onSelect(item.caseId),
          ),
      ],
    );
  }
}
