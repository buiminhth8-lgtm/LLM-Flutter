class NovelStudioRouteGuard {
  const NovelStudioRouteGuard(this.capabilities);

  final List<dynamic> capabilities;

  bool isAvailable(String name) => capabilities.any((item) {
    if (item is! Map) {
      return false;
    }
    return item['name'] == name &&
        (item['status'] == 'available' || item['status'] == 'partial') &&
        item['frontend_exposed'] == true;
  });
}
