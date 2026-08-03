import 'package:flutter/material.dart';

import '../evaluation_api_client.dart';
import '../models/manual_evaluation_score_dto.dart';

class EvaluationManualScorePanel extends StatefulWidget {
  const EvaluationManualScorePanel({
    super.key,
    required this.scores,
    required this.onSave,
  });

  final List<ManualEvaluationScoreDto> scores;
  final ValueChanged<ManualEvaluationScoreRequest> onSave;

  @override
  State<EvaluationManualScorePanel> createState() =>
      _EvaluationManualScorePanelState();
}

class _EvaluationManualScorePanelState
    extends State<EvaluationManualScorePanel> {
  final _reviewer = TextEditingController();
  final _overall = TextEditingController(text: '4.0');
  final _style = TextEditingController(text: '4.0');
  final _character = TextEditingController(text: '4.0');
  final _plot = TextEditingController(text: '4.0');
  final _notes = TextEditingController();

  @override
  void dispose() {
    _reviewer.dispose();
    _overall.dispose();
    _style.dispose();
    _character.dispose();
    _plot.dispose();
    _notes.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('人工评估', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          TextField(
            key: const Key('evaluation-manual-reviewer'),
            controller: _reviewer,
            decoration: const InputDecoration(
              labelText: '审阅人 ID',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(child: _scoreField('总分 1-5', _overall, 'overall')),
              const SizedBox(width: 8),
              Expanded(child: _scoreField('风格', _style, 'style')),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(child: _scoreField('人物', _character, 'character')),
              const SizedBox(width: 8),
              Expanded(child: _scoreField('剧情', _plot, 'plot')),
            ],
          ),
          const SizedBox(height: 8),
          TextField(
            key: const Key('evaluation-manual-notes'),
            controller: _notes,
            minLines: 3,
            maxLines: 6,
            decoration: const InputDecoration(
              labelText: '人工备注',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 8),
          FilledButton.icon(
            key: const Key('evaluation-save-manual-score'),
            onPressed: () => widget.onSave(
              ManualEvaluationScoreRequest(
                reviewerId: _reviewer.text.trim(),
                overallScore: _score(_overall),
                dimensions: {
                  if (_score(_style) != null) 'style': _score(_style)!,
                  if (_score(_character) != null)
                    'character': _score(_character)!,
                  if (_score(_plot) != null) 'plot': _score(_plot)!,
                },
                notes: _notes.text.trim(),
              ),
            ),
            icon: const Icon(Icons.rate_review_outlined),
            label: const Text('保存人工评分'),
          ),
          const Divider(height: 20),
          Text('已保存评分（${widget.scores.length}）'),
          for (final score in widget.scores.take(5))
            ListTile(
              dense: true,
              title: Text(
                score.overallScore == null
                    ? '暂无总分'
                    : '总分 ${score.overallScore!.toStringAsFixed(1)}',
              ),
              subtitle: Text(score.notes ?? score.reviewerId ?? ''),
            ),
        ],
      ),
    ),
  );

  Widget _scoreField(
    String label,
    TextEditingController controller,
    String suffix,
  ) => TextField(
    key: Key('evaluation-score-$suffix'),
    controller: controller,
    keyboardType: const TextInputType.numberWithOptions(decimal: true),
    decoration: InputDecoration(
      labelText: label,
      border: const OutlineInputBorder(),
    ),
  );

  static double? _score(TextEditingController controller) {
    final value = double.tryParse(controller.text.trim());
    if (value == null) {
      return null;
    }
    if (value < 1) {
      return 1;
    }
    if (value > 5) {
      return 5;
    }
    return value;
  }
}
