import 'package:flutter/material.dart';

class RevisionEditor extends StatelessWidget {
  const RevisionEditor({
    super.key,
    required this.originalText,
    required this.editedController,
    required this.onChanged,
  });

  final String originalText;
  final TextEditingController editedController;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Expanded(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: _TextPanel(
                title: 'Model Original',
                child: SelectableText(
                  originalText.isEmpty ? 'No original text.' : originalText,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _TextPanel(
                title: 'Human Edited',
                scrollable: false,
                child: TextField(
                  key: const Key('revision-edited-text'),
                  controller: editedController,
                  minLines: null,
                  maxLines: null,
                  expands: true,
                  textAlignVertical: TextAlignVertical.top,
                  onChanged: onChanged,
                  decoration: const InputDecoration.collapsed(
                    hintText: 'Edit the revision text here.',
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    ],
  );
}

class _TextPanel extends StatelessWidget {
  const _TextPanel({
    required this.title,
    required this.child,
    this.scrollable = true,
  });

  final String title;
  final Widget child;
  final bool scrollable;

  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: BoxDecoration(
      border: Border.all(color: Theme.of(context).dividerColor),
      borderRadius: BorderRadius.circular(8),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 8),
          child: Text(title, style: Theme.of(context).textTheme.titleSmall),
        ),
        const Divider(height: 1),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: scrollable ? SingleChildScrollView(child: child) : child,
          ),
        ),
      ],
    ),
  );
}
