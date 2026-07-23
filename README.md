# 批量查图快速改图工具

一个用 Python + Tkinter 写的本地图片审核和快速处理工具，主要用于批量检查透明底预览图，并对当前图片做常见的小修小改。

## 直接下载

- [Mac（Apple Silicon，`.dmg`）](https://github.com/Frank-jpeg/batch-image-review-editor/releases/latest/download/batch-image-review-editor-macos-arm64.dmg)
- [Mac（Apple Silicon，解压即 app 的 `.zip`）](https://github.com/Frank-jpeg/batch-image-review-editor/releases/latest/download/batch-image-review-editor-macos-arm64.app.zip)
- [Windows 64 位（`.exe`）](https://github.com/Frank-jpeg/batch-image-review-editor/releases/latest/download/batch-image-review-editor-windows-x64.exe)

每次推送到 `main`，GitHub Actions 会自动重新打包并更新上述“最新版”下载文件。

`.app` 在 Mac 里实际是一个特殊文件夹，GitHub 不能直接把它作为单个附件上传，所以提供 DMG 和 ZIP 两种外壳。ZIP 解压后直接得到 `.app`；DMG 打开后把 `.app` 拖到“应用程序”即可。

Mac 第一次打开未签名 app 时，如系统拦截，在 Finder 里按住 Control 点 app，再选“打开”即可。这相当于 Windows 第一次运行陌生 `.exe` 时的安全提示。

Windows 第一次运行未签名 `.exe` 时，SmartScreen 也可能提示风险；确认下载来源是本仓库后，点“更多信息”再点“仍要运行”。

## 功能

- 批量浏览图片，支持上一张、下一张、跳转指定序号。
- 一键打开当前图，也可以直接用 Photoshop 打开当前图。
- 支持反相、转纯白、吸管填色、黑/近黑转白、加粗、加白边。
- 支持矩形选区、自由选区、橡皮擦和吸管填色。
- 支持删除预览图，并把上一层同名原图移动到回退目录；删除也可在本次运行内撤销。
- Photoshop 修改保存后，可回到工具里按 `F5` 刷新当前图。
- 查完后可把当前文件夹自动标记为 `（已查图）`。

## 使用方式

运行源码版：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/抠图查图处理_mac.py
```

Mac 新手可以把 `.venv` 理解成 Windows 里某个项目自己的 Python 环境，装依赖只影响这个项目。

## 图片目录规则

工具默认按这种结构工作：

```text
父文件夹/
  原图1.png
  原图2.png
  透明背景/
    原图1.png
    原图2.png
```

进入工具后选择要检查的子文件夹，例如 `透明背景`。子文件夹里放预览图，它的上一层放同名原图。

## 常用快捷键

- `空格` / `回车`：保留并下一张
- `←` / `Backspace`：上一张
- `O`：用系统默认 App 打开当前图
- `P`：用 Photoshop 打开当前图
- `F5`：刷新当前图
- `R`：矩形选区
- `F`：自由选区
- `E`：橡皮擦
- `C`：吸管填色；有选区时只填充选区
- `[` / `]`：调橡皮擦笔刷大小
- `I`：反相
- `W` / `↑`：转纯白
- `K`：黑/近黑转白
- `B`：加粗 1px
- `2`：加粗 2px
- `N`：加白边
- `D`：删除预览，并把上一层同名原图移到回退目录
- `X` / `↓`：仅删除预览图
- `Ctrl+Z` / `Command+Z` / `U`：撤销
- `Esc`：退出全屏
- `Command+Q`：退出

## 打包

### macOS App

本项目保留了 PyInstaller 配置：

```bash
python -m PyInstaller --noconfirm --clean build/spec/抠图查图处理.spec
```

打包结果会生成在项目根目录的 `dist/`。`.app` 在 macOS 里不是单个 exe，而是一个特殊文件夹，Finder 会把它显示成一个应用。

如果要替换本机安装版，可以把打包后的 `抠图查图处理.app` 复制到：

```text
/Applications/自己做的/
```

### Windows App

Windows 成品由 GitHub Actions 的 Windows 机器自动打包为单文件 `.exe`。本机是 Mac，不能可靠产出可运行的 Windows `.exe`；直接推送到 `main` 即可触发云端构建和发布。

## 依赖

- Python 3.12+
- Pillow
- PyInstaller（仅打包时需要）
- Adobe Photoshop 2024、2025 或 2026（可选，仅 `P` 快捷键需要）

## 说明

这个工具会直接覆盖当前预览图，但本次运行中的修改和删除可以撤销。上传到仓库的只包含源码、图标和打包配置，不包含本地虚拟环境、构建缓存和打包产物。
