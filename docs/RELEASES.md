# 发布与下载

## 用户下载

项目首页的三个链接始终指向 `latest` Release：

- `batch-image-review-editor-macos-arm64.dmg`：Apple Silicon（M 系列）Mac 安装镜像。
- `batch-image-review-editor-macos-arm64.app.zip`：解压后直接得到 `.app`。
- `batch-image-review-editor-windows-x64.exe`：Windows 64 位单文件程序。

Mac 的 `.app` 是文件夹式应用，不能作为单个 GitHub 附件上传，所以提供 DMG 和 ZIP。两个 Mac 包内容相同。

## 自动流程

推送到 `main` 或在 Actions 手动运行 `自动打包并发布最新版` 后，`.github/workflows/publish-latest.yml` 会：

1. 在 `macos-14` 打出 Apple Silicon `.app`，再生成 DMG 和 ZIP。
2. 在 `windows-latest` 打出单文件 Windows x64 EXE。
3. 把 `latest` tag 移到本次提交，更新对应的 GitHub Release，并覆盖三个固定附件。

发布包使用 `release-metadata/source-info.json` 指向公开 GitHub 源码；本地构建保留根目录 `source-info.json` 的本机源码指路。

## 发布后检查

1. GitHub Actions 的三个 job 均为成功。
2. [latest Release](https://github.com/Frank-jpeg/batch-image-review-editor/releases/tag/latest) 只包含三个稳定文件名的附件。
3. README 三个下载链接能打开对应文件。

## 常见问题

- macOS job 找不到图标/源码：检查 spec 是否用 `SPECPATH` 推导路径，不能写 `/Users/...`。
- Release 出现旧附件：工作流会按附件 ID 清除旧的错误命名文件；不要手动改 README 的固定下载文件名。
- 未签名包被系统拦截：Mac 用 Control 点按“打开”；Windows 在确认来源后经 SmartScreen 的“更多信息”选择“仍要运行”。
