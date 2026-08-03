# 下载生命周期

下载由后台 Job 执行，当前远程来源以 ModelScope 为主。

## 状态

- created
- running
- cancelling
- cancelled
- succeeded
- failed

## 行为

- 进度未知时不伪造百分比。
- 取消是协作式请求。
- 重试创建新的后台任务。
- 删除下载记录不删除模型文件。
- 临时目录和缓存由存储清理能力处理。

## Flutter

下载页显示提供方、模型 ID、revision、允许/忽略模式、进度、速度、ETA、错误复制和完成后查看模型。
