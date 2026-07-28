# LLM-Studio Windows Packaging

本阶段优先交付可复现的便携目录版启动流程，不把 PyTorch、CUDA、bitsandbytes、llama.cpp 和模型权重强行打入单文件 EXE。

推荐结构：

```text
LLM-Studio/
  .venv/
  scripts/
  config.yaml
  data/
  llm_studio/
```

模型、LoRA、RAG 索引、Benchmark 报告和诊断包都保存在用户数据目录或 `data/` 下，升级应用代码时默认保留。

如需尝试 PyInstaller，请先在干净 Windows 11 + Python 3.12 虚拟环境中验证 `scripts/doctor.ps1`、Flutter Desktop 启动和小模型加载。若动态依赖收集失败，应回退到虚拟环境启动器方案。
