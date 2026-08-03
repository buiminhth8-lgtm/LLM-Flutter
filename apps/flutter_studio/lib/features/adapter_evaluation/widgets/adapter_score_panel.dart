import 'package:flutter/material.dart';

import '../models/adapter_eval_score_dto.dart';

class AdapterScorePanel extends StatefulWidget {
  const AdapterScorePanel({super.key, this.initialScore, required this.onSave});

  final AdapterEvalScoreDto? initialScore;
  final ValueChanged<AdapterEvalScoreRequest> onSave;

  @override
  State<AdapterScorePanel> createState() => _AdapterScorePanelState();
}

class _AdapterScorePanelState extends State<AdapterScorePanel> {
  String _winner = 'none';
  int _baseScore = 3;
  int _adapterScore = 3;
  final _notes = TextEditingController();

  @override
  void initState() {
    super.initState();
    _syncScore();
  }

  @override
  void didUpdateWidget(covariant AdapterScorePanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialScore?.scoreId != widget.initialScore?.scoreId) {
      _syncScore();
    }
  }

  void _syncScore() {
    final score = widget.initialScore;
    _winner = score?.winner ?? 'none';
    _baseScore = score?.baseScore ?? 3;
    _adapterScore = score?.adapterScore ?? 3;
    _notes.text = score?.notes ?? '';
  }

  @override
  void dispose() {
    _notes.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('人工评分', style: Theme.of(context).textTheme.titleMedium),
            DropdownButton<String>(
              key: const Key('adapter-eval-winner'),
              value: _winner,
              items: const [
                DropdownMenuItem(value: 'adapter', child: Text('adapter')),
                DropdownMenuItem(value: 'base', child: Text('base')),
                DropdownMenuItem(value: 'tie', child: Text('tie')),
                DropdownMenuItem(value: 'none', child: Text('none')),
              ],
              onChanged: (value) => setState(() => _winner = value ?? 'none'),
            ),
            Row(
              children: [
                const Text('base_score'),
                Slider(
                  value: _baseScore.toDouble(),
                  min: 1,
                  max: 5,
                  divisions: 4,
                  label: '$_baseScore',
                  onChanged: (value) =>
                      setState(() => _baseScore = value.round()),
                ),
                Text('$_baseScore'),
              ],
            ),
            Row(
              children: [
                const Text('adapter_score'),
                Slider(
                  value: _adapterScore.toDouble(),
                  min: 1,
                  max: 5,
                  divisions: 4,
                  label: '$_adapterScore',
                  onChanged: (value) =>
                      setState(() => _adapterScore = value.round()),
                ),
                Text('$_adapterScore'),
              ],
            ),
            TextField(
              controller: _notes,
              maxLines: 3,
              decoration: const InputDecoration(labelText: 'notes'),
            ),
            const SizedBox(height: 8),
            FilledButton(
              key: const Key('adapter-eval-save-score'),
              onPressed: () => widget.onSave(
                AdapterEvalScoreRequest(
                  winner: _winner,
                  baseScore: _baseScore,
                  adapterScore: _adapterScore,
                  dimensions: {
                    'style': {'base': _baseScore, 'adapter': _adapterScore},
                    'language_quality': {
                      'base': _baseScore,
                      'adapter': _adapterScore,
                    },
                  },
                  notes: _notes.text,
                ),
              ),
              child: const Text('保存评分'),
            ),
          ],
        ),
      ),
    );
  }
}
