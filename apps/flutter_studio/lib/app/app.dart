import 'package:flutter/material.dart';

import 'app_shell.dart';
import 'app_theme.dart';

class LlmStudioApp extends StatelessWidget {
  const LlmStudioApp({
    super.key,
    this.autoRefresh = true,
    this.initialRequiresSetup = false,
  });

  final bool autoRefresh;
  final bool initialRequiresSetup;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'LLM Studio',
      theme: buildStudioTheme(),
      home: StudioShell(
        autoRefresh: autoRefresh,
        initialRequiresSetup: initialRequiresSetup,
      ),
    );
  }
}
