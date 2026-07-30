import 'package:flutter/material.dart';
import 'package:flutter_studio/features/context_assembler/models/context_assembly_result_dto.dart';
import 'package:flutter_studio/features/context_assembler/models/context_budget_dto.dart';
import 'package:flutter_studio/features/context_assembler/models/context_render_preview_dto.dart';
import 'package:flutter_studio/features/context_assembler/widgets/context_render_preview_panel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Render preview displays rendered prompt and hash', (
    tester,
  ) async {
    const assembly = ContextAssemblyResultDto(
      projectId: 'p1',
      mode: 'chapter_generate',
      variables: {'project_title': 'Novel'},
      selectedItems: {},
      budget: ContextBudgetDto(),
      warnings: [],
      contextHash: 'context-hash',
      estimatedTokens: 10,
      estimatedChars: 20,
    );
    const preview = ContextRenderPreviewDto(
      assembly: assembly,
      renderedPrompt: 'Rendered chapter prompt',
      missingVariables: [],
      renderWarnings: [],
      promptHash: 'prompt-hash',
    );

    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: ContextRenderPreviewPanel(preview: preview)),
      ),
    );

    expect(find.text('Rendered chapter prompt'), findsOneWidget);
    expect(find.textContaining('prompt-hash'), findsOneWidget);
    expect(find.byTooltip('Copy rendered prompt'), findsOneWidget);
  });
}
