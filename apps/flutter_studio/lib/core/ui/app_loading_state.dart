import 'package:flutter/material.dart';

import 'app_loading_view.dart';

class AppLoadingState extends StatelessWidget {
  const AppLoadingState({super.key, this.message = 'Loading...'});

  final String message;

  @override
  Widget build(BuildContext context) {
    return AppLoadingView(message: message);
  }
}
