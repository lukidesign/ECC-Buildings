# 可编辑场景母版

| 文件 | 用途 |
| --- | --- |
| `city-apartment.blend` | 城市与公寓共享场景，供连续镜头渲染使用 |
| `city-final.blend` | 城市最终取景场景 |
| `apartment-final.blend` | 公寓最终取景场景 |
| `room.blend` | 电气室静态视图场景 |
| `room-panorama.blend` | 电气室等距柱状全景场景 |
| `product.blend` | 低压开关柜产品示意场景 |

本次仅移动母版，未重新保存或修改模型内容。旧自动备份与非交付中间版本保存在本机 `.local/archive/models/`。

生成脚本见 [scripts/README.md](../scripts/README.md)，制作方式见 [技术与实现方案](../docs/implementation.md)。直接打开母版进行手动渲染前，应检查其保存的输出路径；脚本入口会使用当前目录约定。
