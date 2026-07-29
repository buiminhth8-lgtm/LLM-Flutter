String formatBytes(num? bytes) {
  if (bytes == null) {
    return '未知';
  }
  var value = bytes.toDouble();
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  var unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  final digits = unit == 0 || value >= 10 ? 0 : 1;
  return '${value.toStringAsFixed(digits)} ${units[unit]}';
}

String formatSpeed(num? bytesPerSecond) {
  if (bytesPerSecond == null || bytesPerSecond <= 0) {
    return '速度未知';
  }
  return '${formatBytes(bytesPerSecond)}/s';
}

String formatEta(num? seconds) {
  if (seconds == null || seconds < 0) {
    return '剩余时间未知';
  }
  final total = seconds.round();
  final hours = total ~/ 3600;
  final minutes = (total % 3600) ~/ 60;
  final secs = total % 60;
  if (hours > 0) {
    return '${hours}h ${minutes}m';
  }
  if (minutes > 0) {
    return '${minutes}m ${secs}s';
  }
  return '${secs}s';
}

