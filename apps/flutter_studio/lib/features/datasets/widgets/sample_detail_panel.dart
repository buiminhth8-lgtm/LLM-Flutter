import 'package:flutter/material.dart';

import '../models/training_sample_dto.dart';
import 'sample_status_badge.dart';

class SampleDetailPanel extends StatefulWidget {
  const SampleDetailPanel({
    super.key,
    required this.sample,
    required this.onSave,
    required this.onApprove,
    required this.onReject,
  });

  final TrainingSampleDto? sample;
  final ValueChanged<UpdateSampleRequest> onSave;
  final VoidCallback onApprove;
  final ValueChanged<String?> onReject;

  @override
  State<SampleDetailPanel> createState() => _SampleDetailPanelState();
}

class _SampleDetailPanelState extends State<SampleDetailPanel> {
  final _instruction = TextEditingController();
  final _input = TextEditingController();
  final _output = TextEditingController();
  final _notes = TextEditingController();
  String? _sampleId;

  @override
  void dispose() {
    _instruction.dispose();
    _input.dispose();
    _output.dispose();
    _notes.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final sample = widget.sample;
    _sync(sample);
    if (sample == null) {
      return const Center(child: Text('请选择样本。'));
    }
    return ListView(
      key: const Key('sample-detail-panel'),
      children: [
        Row(
          children: [
            SampleStatusBadge(status: sample.status),
            const Spacer(),
            Text(sample.sampleType),
          ],
        ),
        const SizedBox(height: 8),
        Text('修订：${sample.revisionId ?? '-'}'),
        Text('质量评分：${sample.qualityScore ?? '-'}'),
        if (sample.warnings.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              sample.warnings.map((item) => item['code']).join(', '),
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ),
        const SizedBox(height: 12),
        TextField(
          key: const Key('sample-instruction'),
          controller: _instruction,
          maxLines: 4,
          decoration: const InputDecoration(
            labelText: 'instruction',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          key: const Key('sample-input'),
          controller: _input,
          maxLines: 7,
          decoration: const InputDecoration(
            labelText: 'input',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          key: const Key('sample-output'),
          controller: _output,
          maxLines: 8,
          decoration: const InputDecoration(
            labelText: 'output',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _notes,
          maxLines: 2,
          decoration: const InputDecoration(
            labelText: '审阅备注',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        FilledButton.icon(
          key: const Key('sample-save'),
          onPressed: () => widget.onSave(
            UpdateSampleRequest(
              instruction: _instruction.text,
              input: _input.text,
              output: _output.text,
              reviewNotes: _notes.text,
            ),
          ),
          icon: const Icon(Icons.save_outlined),
          label: const Text('保存样本'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          key: const Key('sample-approve'),
          onPressed: widget.onApprove,
          icon: const Icon(Icons.verified_outlined),
          label: const Text('批准样本'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          key: const Key('sample-reject'),
          onPressed: () => widget.onReject(_notes.text.trim()),
          icon: const Icon(Icons.block_outlined),
          label: const Text('拒绝样本'),
        ),
      ],
    );
  }

  void _sync(TrainingSampleDto? sample) {
    if (sample == null || _sampleId == sample.sampleId) {
      return;
    }
    _sampleId = sample.sampleId;
    _instruction.text = sample.instruction;
    _input.text = sample.input;
    _output.text = sample.output;
    _notes.text = sample.reviewNotes ?? '';
  }
}
