import 'package:flutter/material.dart';

import '../../prompt_studio/models/prompt_template_dto.dart';

class WritingPromptSelector extends StatelessWidget {
  const WritingPromptSelector({
    super.key,
    required this.templates,
    required this.value,
    required this.onChanged,
  });

  final List<PromptTemplateDto> templates;
  final String? value;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) => DropdownButtonFormField<String>(
    key: const Key('writing-prompt-selector'),
    initialValue: value,
    isExpanded: true,
    items: [
      for (final template in templates)
        DropdownMenuItem(
          value: template.id,
          child: Text('${template.name} · ${template.type}'),
        ),
    ],
    onChanged: onChanged,
    decoration: const InputDecoration(
      labelText: 'Prompt 模板',
      border: OutlineInputBorder(),
    ),
  );
}
