import 'package:flutter_studio/app/shell_navigation_controller.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('select changes current page and notifies listeners', () {
    final controller = ShellNavigationController();
    var notifications = 0;
    controller.addListener(() => notifications += 1);

    controller.select(3);
    controller.select(3);
    controller.select(9);

    expect(controller.pageIndex, 9);
    expect(notifications, 2);
  });
}
