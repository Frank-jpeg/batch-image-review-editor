# 项目规则

- 主程序是 `src/抠图查图处理_mac.py`；它同时服务 macOS 和 Windows，不要按文件名误判为仅 Mac。
- 保持平台分支：macOS 的 Dock/废纸篓逻辑只在 `darwin` 执行；Windows 的配置目录、回收站和 Photoshop 路径只在 `win32` 执行。
- macOS 打包入口是 `build/spec/抠图查图处理.spec`。图标、入口和数据文件必须从 `SPECPATH` 推导，禁止写本机绝对路径。
- 本地打包使用根目录 `source-info.json`；GitHub 发布包使用 `release-metadata/source-info.json`，两者都必须保留。
- 推送 `main` 会运行 `.github/workflows/publish-latest.yml`，更新 `latest` Release 的三个固定附件。改附件名时必须同时更新 README 下载链接和工作流清理逻辑。
- 生成的 `dist/`、`build/`、虚拟环境和安装包不提交。

## 验证

```bash
python -m py_compile src/抠图查图处理_mac.py
python -m PyInstaller --noconfirm --clean build/spec/抠图查图处理.spec
```
