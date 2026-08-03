import 'package:flutter/material.dart';

import '../models/adapter_eval_create_request_dto.dart';

class AdapterEvalCreateCaseDialog extends StatefulWidget {
  const AdapterEvalCreateCaseDialog({
    super.key,
    required this.projectId,
    required this.onCreate,
  });

  final String? projectId;
  final ValueChanged<CreateAdapterEvalCaseRequest> onCreate;

  @override
  State<AdapterEvalCreateCaseDialog> createState() =>
      _AdapterEvalCreateCaseDialogState();
}

class _AdapterEvalCreateCaseDialogState
    extends State<AdapterEvalCreateCaseDialog> {
  final _title = TextEditingController(text: 'Base vs Adapter case');
  final _project = TextEditingController();
  final _chapter = TextEditingController();
  final _template = TextEditingController();
  final _goal = TextEditingController(text: 'Compare continuation quality.');
  final _style = TextEditingController(text: '紧张、细节丰富');
  final _pov = TextEditingController(text: '第三人称');
  final _maxTokens = TextEditingController(text: '512');

  @override
  void initState() {
    super.initState();
    _project.text = widget.projectId ?? '';
  }

  @override
  void dispose() {
    _title.dispose();
    _project.dispose();
    _chapter.dispose();
    _template.dispose();
    _goal.dispose();
    _style.dispose();
    _pov.dispose();
    _maxTokens.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Create Evaluation Case'),
      content: SizedBox(
        width: 560,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _title,
                decoration: const InputDecoration(labelText: 'title'),
              ),
              TextField(
                controller: _project,
                decoration: const InputDecoration(labelText: 'project_id'),
              ),
              TextField(
                controller: _chapter,
                decoration: const InputDecoration(labelText: 'chapter_id'),
              ),
              TextField(
                controller: _template,
                decoration: const InputDecoration(
                  labelText: 'prompt_template_id',
                ),
              ),
              TextField(
                controller: _goal,
                decoration: const InputDecoration(
                  labelText: 'current_chapter_goal',
                ),
              ),
              TextField(
                controller: _style,
                decoration: const InputDecoration(labelText: 'style'),
              ),
              TextField(
                controller: _pov,
                decoration: const InputDecoration(labelText: 'pov'),
              ),
              TextField(
                controller: _maxTokens,
                decoration: const InputDecoration(labelText: 'max_tokens'),
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        FilledButton(
          key: const Key('adapter-eval-create-case-submit'),
          onPressed: () {
            widget.onCreate(
              CreateAdapterEvalCaseRequest(
                title: _title.text,
                projectId: _project.text,
                chapterId: _chapter.text,
                templateId: _template.text,
                mode: 'chapter_generate',
                userVariables: {
                  'current_chapter_goal': _goal.text,
                  'style': _style.text,
                  'pov': _pov.text,
                },
                generationParams: {
                  'max_tokens': int.tryParse(_maxTokens.text) ?? 512,
                  'temperature': 0.8,
                  'top_p': 0.9,
                },
                targetLength: const {
                  'unit': 'chars',
                  'min': 1,
                  'max': 800,
                  'strategy': 'soft',
                },
              ),
            );
            Navigator.pop(context);
          },
          child: const Text('Create Case'),
        ),
      ],
    );
  }
}
