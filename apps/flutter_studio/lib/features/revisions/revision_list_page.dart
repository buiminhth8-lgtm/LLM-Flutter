import 'package:flutter/material.dart';

import '../../core/ui/app_section_header.dart';
import 'revision_controller.dart';
import 'widgets/revision_status_badge.dart';

class RevisionListPage extends StatelessWidget {
  const RevisionListPage({super.key, required this.controller});

  final RevisionController controller;

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: controller,
    builder: (context, _) {
      final state = controller.state;
      return Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppSectionHeader(
              title: 'Revision Records',
              subtitle:
                  'Human edited assets created from writing generations or drafts.',
              actions: [
                IconButton.filledTonal(
                  onPressed: state.loading ? null : controller.refresh,
                  icon: const Icon(Icons.refresh),
                  tooltip: 'Refresh',
                ),
              ],
            ),
            if (state.loading) const LinearProgressIndicator(),
            const SizedBox(height: 12),
            Expanded(
              child: ListView(
                children: [
                  for (final revision in state.revisions)
                    ListTile(
                      leading: const Icon(Icons.rate_review_outlined),
                      title: Text(revision.revisionId),
                      subtitle: Text(
                        '${revision.source} · score ${revision.userScore ?? '-'} · ${revision.createdAt}',
                      ),
                      trailing: RevisionStatusBadge(status: revision.status),
                      onTap: () => controller.openRevision(revision.revisionId),
                    ),
                ],
              ),
            ),
          ],
        ),
      );
    },
  );
}
