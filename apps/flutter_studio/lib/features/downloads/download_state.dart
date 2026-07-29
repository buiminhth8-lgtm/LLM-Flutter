import '../../core/models/dto.dart';

class DownloadState {
  const DownloadState({this.downloads = const []});

  final List<DownloadTaskDto> downloads;

  bool get hasRunningDownloads => downloads.any((item) => item.isRunning);
}
