import 'package:flutter/material.dart';

import '../../novels/models/novel_project_dto.dart';

class WritingProjectSelector extends StatelessWidget {
  const WritingProjectSelector({
    super.key,
    required this.projects,
    required this.value,
    required this.onChanged,
  });

  final List<NovelProjectDto> projects;
  final String? value;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) => DropdownButtonFormField<String>(
    key: const Key('writing-project-selector'),
    initialValue: value,
    isExpanded: true,
    items: [
      for (final project in projects)
        DropdownMenuItem(value: project.id, child: Text(project.title)),
    ],
    onChanged: onChanged,
    decoration: const InputDecoration(
      labelText: '小说项目',
      border: OutlineInputBorder(),
    ),
  );
}
