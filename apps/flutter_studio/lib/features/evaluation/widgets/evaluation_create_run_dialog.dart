import 'package:flutter/material.dart';

import '../evaluation_api_client.dart';
import 'evaluation_target_selector.dart';

class EvaluationCreateRunDialog extends StatefulWidget {
  const EvaluationCreateRunDialog({
    super.key,
    required this.onCreate,
    this.initialTargetType = 'chapter',
    this.initialTargetId = '',
    this.initialProjectId = '',
    this.initialChapterId = '',
  });

  final ValueChanged<CreateEvaluationRunRequest> onCreate;
  final String initialTargetType;
  final String initialTargetId;
  final String initialProjectId;
  final String initialChapterId;

  @override
  State<EvaluationCreateRunDialog> createState() =>
      _EvaluationCreateRunDialogState();
}

class _EvaluationCreateRunDialogState extends State<EvaluationCreateRunDialog> {
  late final _name = TextEditingController(text: '小说评估');
  final _description = TextEditingController();
  late final _targetId = TextEditingController(text: widget.initialTargetId);
  late final _projectId = TextEditingController(text: widget.initialProjectId);
  late final _chapterId = TextEditingController(text: widget.initialChapterId);
  final _localModel = TextEditingController();
  late String _targetType = widget.initialTargetType;
  final _enabled = <String>{...defaultEvaluationEvaluators};
  bool _useLocalModelJudge = false;

  @override
  void dispose() {
    _name.dispose();
    _description.dispose();
    _targetId.dispose();
    _projectId.dispose();
    _chapterId.dispose();
    _localModel.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('创建评估运行'),
    content: SizedBox(
      width: 640,
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              key: const Key('evaluation-run-name'),
              controller: _name,
              decoration: const InputDecoration(
                labelText: '运行名称',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _description,
              decoration: const InputDecoration(
                labelText: '描述',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            EvaluationTargetSelector(
              targetType: _targetType,
              targetIdController: _targetId,
              projectIdController: _projectId,
              chapterIdController: _chapterId,
              onTargetTypeChanged: (value) =>
                  setState(() => _targetType = value),
            ),
            const SizedBox(height: 14),
            Text('评估器', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 6),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                for (final entry in evaluationEvaluatorLabels.entries)
                  if (entry.key != 'local_model_judge')
                    FilterChip(
                      key: Key('evaluation-evaluator-${entry.key}'),
                      label: Text(entry.value),
                      selected: _enabled.contains(entry.key),
                      onSelected: (value) => setState(() {
                        if (value) {
                          _enabled.add(entry.key);
                        } else {
                          _enabled.remove(entry.key);
                        }
                      }),
                    ),
              ],
            ),
            const SizedBox(height: 10),
            SwitchListTile(
              key: const Key('evaluation-local-model-judge'),
              contentPadding: EdgeInsets.zero,
              value: _useLocalModelJudge,
              title: const Text('使用本地模型裁判'),
              subtitle: const Text('可选；仅使用本地 Runtime。'),
              onChanged: (value) => setState(() {
                _useLocalModelJudge = value;
                if (value) {
                  _enabled.add('local_model_judge');
                } else {
                  _enabled.remove('local_model_judge');
                }
              }),
            ),
            TextField(
              key: const Key('evaluation-local-model-id'),
              controller: _localModel,
              enabled: _useLocalModelJudge,
              decoration: const InputDecoration(
                labelText: '本地裁判模型 ID',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            const Text('评估只读取现有小说工作台资产，不会重写章节、创建训练样本或启动微调。'),
          ],
        ),
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.of(context).pop(),
        child: const Text('取消'),
      ),
      FilledButton(
        key: const Key('evaluation-create-run-submit'),
        onPressed: _enabled.isEmpty
            ? null
            : () {
                Navigator.of(context).pop();
                final targetId = _targetId.text.trim();
                widget.onCreate(
                  CreateEvaluationRunRequest(
                    name: _name.text.trim().isEmpty
                        ? '小说评估'
                        : _name.text.trim(),
                    description: _description.text.trim(),
                    targetType: _targetType,
                    targetId: targetId,
                    projectId: _projectId.text.trim(),
                    chapterId: _chapterId.text.trim(),
                    generationId: _targetType == 'generation' ? targetId : null,
                    revisionId: _targetType == 'revision' ? targetId : null,
                    adapterEvalSessionId: _targetType == 'adapter_eval_session'
                        ? targetId
                        : null,
                    memoryRetrievalId: _targetType == 'memory_retrieval'
                        ? targetId
                        : null,
                    enabledEvaluators: _enabled.toList(growable: false),
                    useLocalModelJudge: _useLocalModelJudge,
                    localModelId: _localModel.text.trim(),
                  ),
                );
              },
        child: const Text('运行评估'),
      ),
    ],
  );
}
