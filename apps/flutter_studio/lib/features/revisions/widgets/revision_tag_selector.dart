import 'package:flutter/material.dart';

import '../models/revision_tag.dart';

class RevisionTagSelector extends StatelessWidget {
  const RevisionTagSelector({
    super.key,
    required this.values,
    required this.onChanged,
  });

  final List<String> values;
  final ValueChanged<List<String>> onChanged;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text('修改标签', style: Theme.of(context).textTheme.titleSmall),
      const SizedBox(height: 8),
      Wrap(
        spacing: 8,
        runSpacing: 6,
        children: [
          for (final tag in revisionTags)
            FilterChip(
              key: Key('revision-tag-${tag.value}'),
              label: Text(tag.label),
              selected: values.contains(tag.value),
              onSelected: (selected) {
                final next = [...values];
                if (selected) {
                  next.add(tag.value);
                } else {
                  next.remove(tag.value);
                }
                onChanged(next);
              },
            ),
        ],
      ),
    ],
  );
}
