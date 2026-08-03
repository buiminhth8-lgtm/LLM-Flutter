# Diagnostics Guide

## API

- `GET /v1/diagnostics/health`
- `GET /v1/diagnostics/system`
- `GET /v1/diagnostics/capabilities`
- `GET /v1/diagnostics/preview`
- `POST /v1/diagnostics/export`

## Flutter

Diagnostics 页面显示 runtime、health、system、capabilities，并可导出脱敏诊断包。

## 脱敏规则

后端负责最终脱敏。诊断包只保存摘要：

- 路径显示为 `<redacted-...>/name`；
- secret 字段显示为 `<redacted>`；
- 不包含模型权重、adapter 权重、checkpoint；
- 不包含正文、RAG 文档正文或 API Key。
