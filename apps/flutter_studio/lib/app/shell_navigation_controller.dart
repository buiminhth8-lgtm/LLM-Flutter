import 'package:flutter/foundation.dart';

class ShellNavigationController extends ChangeNotifier {
  int _pageIndex = 0;

  int get pageIndex => _pageIndex;

  void select(int index) {
    if (index == _pageIndex) {
      return;
    }
    _pageIndex = index;
    notifyListeners();
  }
}
