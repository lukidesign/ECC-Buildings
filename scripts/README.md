# 媒体生产脚本

从仓库根目录运行。网页的开发和构建命令仍在 `web/package.json` 中。

| 脚本 | 输入 | 输出 |
| --- | --- | --- |
| `blender/build_scenes.py` | 程序化场景参数、`web/components/landscape/room-view.json` | `models/` 母版、`.local/renders/` 图像和元数据，或 `.local/evidence/gray/` 灰模证据 |
| `blender/render_delivery.py` | `models/city-apartment.blend` | `.local/renders/` 城市/公寓端点、`models/*-final.blend`；`--motion` 输出 `.local/work/transition/` |
| `assets/export_assets.mjs` | `.local/renders/` PNG 和 JSON | `web/public/assets/` WebP、热点 JSON 和 manifest |

```sh
blender --background --python scripts/blender/build_scenes.py -- --scene room --quality final
blender --background --python scripts/blender/build_scenes.py -- --scene room --view panorama --quality final --cpu
blender --background --python scripts/blender/render_delivery.py -- --motion
node scripts/assets/export_assets.mjs
```

Blender 命令要求本机安装 Blender，并可通过 `blender` 调用。导出脚本使用 `web/` 的 Node 依赖，先在 `web/` 执行 `npm ci`。视频编码仍需另外执行；图片导出不会生成 MP4。

脚本会更新同名模型或输出文件，手工修改过母版后请先保存副本。`render_delivery.py` 仍使用 Metal 设备配置，跨平台需要适配。Blender 母版内部保存的历史输出路径未改写，推荐通过这里的脚本覆盖输出位置。

过往调试、一次性品牌迁移、立方体全景实验等脚本保留在本机 `.local/archive/scripts/`，不属于当前生产入口。
