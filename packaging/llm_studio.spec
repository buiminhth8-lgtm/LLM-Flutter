# PyInstaller spec scaffold. It intentionally excludes model weights and user data.

block_cipher = None

a = Analysis(
    ["llm_studio/cli.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("config.yaml", "."),
        ("configs", "configs"),
        ("requirements", "requirements"),
    ],
    hiddenimports=[],
    excludes=[
        "torch",
        "bitsandbytes",
        "llama_cpp",
        "gptqmodel",
        "easyocr",
        "paddleocr",
    ],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="llm-studio", console=True)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name="LLM-Studio")
