import 'package:flutter/material.dart';

class RevisionAutosaveIndicator extends StatelessWidget {
  const RevisionAutosaveIndicator({
    super.key,
    required this.autosaving,
    required this.lastAutosaveAt,
  });

  final bool autosaving;
  final String? lastAutosaveAt;

  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      if (autosaving)
        const SizedBox(
          width: 16,
          height: 16,
          child: CircularProgressIndicator(strokeWidth: 2),
        )
      else
        const Icon(Icons.cloud_done_outlined, size: 18),
      const SizedBox(width: 6),
      Text(
        autosaving
            ? '自动保存中'
            : lastAutosaveAt == null
            ? '尚未自动保存'
            : '$lastAutosaveAt 已自动保存',
      ),
    ],
  );
}
