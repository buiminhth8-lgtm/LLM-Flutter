# Windows 真实运行验收

本文用于记录 Windows 桌面端真实运行验收。不要把未执行项目填为 PASS。

## 环境准备

1. 安装 Python 3.11+。
2. 在仓库根目录创建并启用虚拟环境：

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. 安装后端依赖：

   ```powershell
   python -m pip install --upgrade pip setuptools wheel
   python -m pip install -r requirements\base.txt
   python -m pip install -r requirements\web.txt
   python -m pip install -e .
   ```

4. 启动后端：

   ```powershell
   python -m llm_studio.server --host 127.0.0.1 --port 8000
   ```

5. 另开终端验证：

   ```powershell
   curl http://127.0.0.1:8000/health
   curl http://127.0.0.1:8000/v1/capabilities
   ```

6. 进入 Flutter 项目：

   ```powershell
   cd apps\flutter_studio
   flutter pub get
   flutter run -d windows
   ```

## 功能验收步骤

1. 启动应用。
2. 在 Settings 中确认 API Base URL 指向本地后端。
3. 验证 Settings 可以连接后端，并能查看脱敏后的后端日志。
4. 验证 Models 页面可以扫描模型。
5. 验证 Chat 页面在未加载模型时禁用输入并提示先加载模型。
6. 验证加载模型后 Chat 显示当前模型。
7. 验证 Downloads 页面显示下载任务状态、进度、速度和 ETA；总大小未知时不显示伪造百分比。
8. 验证 Downloads 取消后显示“取消请求已提交”或真实终态。
9. 验证 Jobs 页面可显示任务类型、状态、错误码和详情。
10. 验证 RAG 路径访问被拒绝时显示明确错误。
11. 验证 Diagnostics 可以导出脱敏诊断包。
12. 解压诊断包，确认不包含 API Key、Token、Cookie、模型权重或 RAG 文档正文。
13. 验证关闭应用后是否按 Settings 中的退出行为关闭本地后端。

## 验收结果表

| 项目 | 结果 | 备注 |
|---|---|---|
| 后端启动 | PASS/FAIL | |
| /health | PASS/FAIL | |
| /v1/capabilities | PASS/FAIL | |
| Flutter analyze | PASS/FAIL | |
| Flutter test | PASS/FAIL | |
| Flutter build windows | PASS/FAIL | |
| Windows 运行 | PASS/FAIL | |
| Settings 连接后端 | PASS/FAIL | |
| 后端自动启动 | PASS/FAIL | |
| Models 扫描 | PASS/FAIL | |
| Chat 无模型禁用输入 | PASS/FAIL | |
| 下载进度 | PASS/FAIL | |
| Jobs 页面 | PASS/FAIL | |
| 诊断包脱敏 | PASS/FAIL | |
| 退出行为 | PASS/FAIL | |
