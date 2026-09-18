# 贡献与维护指南

## 目录与修改范围

请先阅读 [项目 README](README.md) 和 [目录管理说明](docs/repository-layout.md)。应用开发在 `web/`，媒体生产脚本在 `scripts/`，可编辑模型在 `models/`，维护文档在 `docs/`。

保持变更聚焦，并同步更新受影响的中英文文案、媒体元数据和文档。不要将本地缓存、原始渲染、验收截图、虚拟环境或历史归档提交到仓库。

## 验证

开发完成后先进行对抗式审查，检查失败路径、深层链接、前进后退、语言切换和静态部署前缀，再执行与修改相关的验证。

前端变更可在 `web/` 执行：

```sh
node --experimental-strip-types --test tests/*.test.mjs
npx tsc --noEmit
npm run build:pages
```

涉及原有框架入口时另执行 `npm run build`。纯文档变更检查内容、相对链接、图片与 Markdown 格式即可。媒体或相机修改需补充场景外观、完整取景和热点对应关系检查。

## 提交与评审

- 使用说明目的的提交标题，例如 `docs: explain panorama rendering` 或 `fix: preserve scene paths on Pages`。
- 提交前查看 `git status`、`git diff` 和 `git diff --check`。
- Pull Request 说明解决的问题、最终行为、验证结果以及尚未验证的部分。
- `.editorconfig` 规定 UTF-8、LF 和基本缩进；`.gitattributes` 规定文本与二进制属性，避免把媒体当作文本处理。
- `main` 上的推送会触发 Pages 发布，发布前应确认提交范围。

## English quick guide

Keep application code in `web/`, production scripts in `scripts/`, editable scene masters in `models/`, and documentation in `docs/`. Keep `.local/`, tool environments, and build caches out of Git. Review failure cases before running checks appropriate to the change. Explain the problem, behavior, and validation in each pull request. Pushes to `main` trigger the Pages deployment workflow.
