import 'package:flutter/material.dart';

ThemeData buildStudioTheme() {
  return ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff2563eb)),
    scaffoldBackgroundColor: const Color(0xfff7f8fb),
    cardTheme: const CardThemeData(elevation: 0),
  );
}
