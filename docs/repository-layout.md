# 仓库目录与文件管理

本约定针对 ECC Buildings 的实际构建和媒体生产流程制定。GitHub 并没有强制所有项目采用同一种目录结构；本仓库按应用、文档、生产脚本、可编辑模型与本地工作数据划分。

## 当前目录

```text
ABB01/
├── .github/                 # Pages 发布工作流与 PR 模板
├── .editorconfig            # 编辑器文本格式约定
├── .gitattributes           # 文本换行及二进制文件属性
├── .gitignore               # 本地数据、环境与缓存排除规则
├── README.md                # 中英文项目入口
├── CONTRIBUTING.md          # 修改、验证与提交说明
├── docs/                    # 当前技术与维护文档
│   ├── README.md
│   ├── implementation.md
│   └── repository-layout.md
├── scripts/                 # 可维护的媒体生产脚本
│   ├── README.md
│   ├── blender/
│   │   ├── build_scenes.py
│   │   └── render_delivery.py
│   └── assets/export_assets.mjs
├── models/                  # 六份可编辑 Blender 场景母版
│   └── README.md
├── web/                     # React 应用、测试、运行素材与构建配置
│   ├── app/
│   ├── components/
│   ├── public/assets/       # 网页直接使用的 WebP、MP4 与 JSON
│   ├── static-preview/      # GitHub Pages 静态入口
│   ├── scripts/             # 前端构建与执行工具
│   └── tests/
├── .local/                  # 本机保留，Git 忽略
│   ├── README.md
│   ├── renders/             # 原始 PNG 及渲染元数据
│   ├── evidence/            # 截图、对照图、验收记录
│   ├── work/                # 动画帧及临时工作数据
│   ├── archive/             # 历史规格、旧脚本、备份模型与模板代码
│   └── organization/        # 本次迁移脚本、路径清单与原文件哈希
└── tools/                   # 本机工具与已有 Python 虚拟环境，Git 忽略
```

`web/node_modules/`、`web/dist/`、`web/pages-dist/`、`.wrangler/` 等仍可在本机存在，由忽略规则排除。它们保留在框架期望的位置，不作为源码提交。隐藏目录 `.local/` 可在文件管理器显示隐藏文件后查看。

## 文件归属与提交边界

| 内容 | 位置 | Git 管理 |
| --- | --- | --- |
| 应用源码、测试和锁文件 | `web/` | 提交 |
| 当前技术方案与维护约定 | `docs/`、根目录 README | 提交 |
| Blender 建模与渲染脚本 | `scripts/blender/` | 提交 |
| 媒体转换脚本 | `scripts/assets/` | 提交 |
| 六份交付场景母版 | `models/` | 提交，作为二进制处理 |
| 网页运行媒体 | `web/public/assets/` | 提交 |
| PNG 原图、连续渲染帧、验收截图 | `.local/` | 不提交 |
| 自动生成的 `city.blend`、`apartment.blend` 和 Blender 备份 | `models/` 或本地归档 | 不提交 |
| 参考分析、历史 SPEC、旧交付清单 | `.local/archive/` | 不提交 |
| 虚拟环境、下载工具、框架缓存 | `tools/`、`web/` 下对应缓存 | 不提交 |
| 环境变量文件、证书和本地数据库 | 各自本地位置 | 按 `.gitignore` 排除 |

`.gitattributes` 声明模型与媒体为二进制；本次未改写 Git 历史，也未切换现有二进制文件的存储方式。`.editorconfig` 只约束后续编辑，没有批量格式化已有源码。

## 本次迁移对照（2026-09-18）

| 原路径 | 当前路径 |
| --- | --- |
| `ECC_Buildings_技术与实现方案.md` | `docs/implementation.md` |
| `source/build_scenes.py` | `scripts/blender/build_scenes.py` |
| `source/render_delivery.py` | `scripts/blender/render_delivery.py` |
| `source/export_assets.mjs` | `scripts/assets/export_assets.mjs` |
| 六份已跟踪 `source/*.blend` | `models/` 下同名文件 |
| `assets/` | `.local/renders/` |
| `evidence/` | `.local/evidence/` |
| `work/` | `.local/work/` |
| 根目录历史分析与 SPEC、`source/PRODUCTION_PLAN.md` | `.local/archive/docs/` |
| `DELIVERY_MANIFEST.json` | `.local/archive/DELIVERY_MANIFEST.json` |
| 其他中间模型和 `.blend1` 备份 | `.local/archive/models/` |
| 原 `source/` 下未纳入交付的阶段性脚本 | `.local/archive/scripts/` |
| 未纳入仓库的前端模板 README、示例、数据库目录与认证辅助文件 | `.local/archive/web-starter/` |

迁移清单位于本机 `.local/organization/moves.json`，记录 43 项移动、515 个文件的原路径与 SHA-256。移动完成时所有文件内容一致；随后对维护中的脚本和文档进行了必要的路径更新，因此这些文本文件不再与迁移前哈希相同。模型、图片、视频及历史记录内容保持不变。

历史归档保留原文和当时的路径、版本与结论，没有把旧验收结论改写成当前结论。归档脚本不属于当前可直接执行的工具链；需要复用时，应先更新其路径、输入和前置条件，再转入 `scripts/`。

`tools/venv` 的命令入口包含原安装路径，因此 `tools/` 保留位置。不要只移动虚拟环境目录；若以后需要调整，应在目标位置重新创建环境。

## 日常维护

1. 新文档放入 `docs/`，在文档索引中加入链接；图片尽量复用已存在的项目资源。
2. 网页使用的最终素材放入 `web/public/assets/`，原始渲染放入 `.local/renders/`。
3. 修改模型后同步更新对应图像、视频和热点元数据，检查相关相机与交互。
4. 提交前查看 `git status` 和差异，确认没有把 `.local/`、工具环境或构建产物加入仓库。
5. 不添加未确认的项目许可证；现有第三方依赖与随库素材的许可证文件继续保留。

根目录的整理不会改变网页路由、Pages 仓库前缀或 `web/` 的工作目录。GitHub Actions 仍在 `web/` 安装依赖并构建静态站点。

未投入使用的数据库模板已归档，对应的 `db:generate` 命令一并移除，避免保留一个依赖已归档配置的入口；现有依赖锁文件未调整。
