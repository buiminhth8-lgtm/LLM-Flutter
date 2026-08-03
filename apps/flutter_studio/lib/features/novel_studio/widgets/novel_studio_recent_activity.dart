import 'package:flutter/material.dart';

class NovelStudioRecentActivity extends StatelessWidget {
  const NovelStudioRecentActivity({
    super.key,
    required this.projectCount,
    required this.chapterCount,
    required this.generationCount,
    required this.revisionCount,
    required this.datasetCount,
    required this.finetuneRunCount,
    required this.evaluationRunCount,
  });

  final int projectCount;
  final int chapterCount;
  final int generationCount;
  final int revisionCount;
  final int datasetCount;
  final int finetuneRunCount;
  final int evaluationRunCount;

  @override
  Widget build(BuildContext context) {
    final stats = [
      ('Projects', projectCount),
      ('Chapters', chapterCount),
      ('Generations', generationCount),
      ('Revisions', revisionCount),
      ('Datasets', datasetCount),
      ('Fine-tune runs', finetuneRunCount),
      ('Evaluation runs', evaluationRunCount),
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Recent activity',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            for (final stat in stats)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Expanded(child: Text(stat.$1)),
                    Text(
                      '${stat.$2}',
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
