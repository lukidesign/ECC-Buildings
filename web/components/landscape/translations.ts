export type Locale = "zh" | "en";
export const LANGUAGE_STORAGE_KEY = "ecc-language";
export const LEGACY_LANGUAGE_STORAGE_KEY = "abb01-language";
export function readSavedLocale(storage: Pick<Storage, "getItem" | "setItem">): Locale | null {
  try {
    const current = storage.getItem(LANGUAGE_STORAGE_KEY);
    if (current === "zh" || current === "en") return current;
    const legacy = storage.getItem(LEGACY_LANGUAGE_STORAGE_KEY);
    if (legacy === "zh" || legacy === "en") {
      try { storage.setItem(LANGUAGE_STORAGE_KEY, legacy); } catch { /* Read-only storage still preserves this session. */ }
      return legacy;
    }
  } catch { /* Unavailable storage falls back to the browser language. */ }
  return null;
}
export function resolveLocale(saved: string | null, browserLanguage: string): Locale {
  if (saved === "zh" || saved === "en") return saved;
  return /^zh(?:-|_|$)/i.test(browserLanguage) ? "zh" : "en";
}
export const zh: Record<string, string> = {
  "Buildings": "建筑场景",
  "Residential | Apartment complex": "住宅 | 公寓楼",
  "Electrical Room": "电气室",
  "LV Switchgear": "低压开关柜",
  "Modular LV switchgear": "模块化低压开关柜",
  "Explore": "探索",
  "Breadcrumb": "面包屑导航",
  "Buildings overview": "建筑总览",
  "Hide navigation": "收起导航",
  "Show navigation": "展开导航",
  "ECC · Spatial Explorer": "ECC · 空间探索",
  "Explore buildings": "探索建筑",
  "Building Applications": "建筑应用",
  "Discover connected spaces.": "探索互联空间。",
  "Start with the apartment complex.": "从公寓楼开始。",
  "Residential": "住宅",
  "Apartment complex": "公寓楼",
  "One building. A complete journey.": "一座建筑，一段完整的探索之旅。",
  "Power Distribution": "配电系统",
  "Explore the electrical systems behind a connected residential building.": "探索智慧住宅背后的电气系统。",
  "Reliable power, from the incoming supply to every connected space.": "从进线电源到每一处互联空间，提供可靠电力。",
  "Scene navigation": "场景导航",
  "01 / THE CITY": "01 / 城市场景",
  "02 / THE BUILDING": "02 / 建筑场景",
  "03 / THE ELECTRICAL ROOM": "03 / 电气室",
  "Explore a connected city, one building at a time.": "逐一走进建筑，探索互联城市。",
  "Step inside the systems that bring a residential building to life.": "走进住宅内部，了解支撑建筑运行的系统。",
  "Discover modular power distribution inside the electrical room.": "探索电气室内的模块化配电系统。",
  "BACK": "返回",
  "Drag to look around · Arrow keys to rotate": "拖动环视 · 方向键旋转",
  "Reset room view": "重置电气室视角",
  "Room view reset": "电气室视角已重置",
  "Select a building to explore": "选择一座建筑开始探索",
  "ECC Spatial Explorer": "ECC 空间探索",
  "Independently modeled study": "独立建模演示",
  "Interactive demonstration": "交互演示",
  "Scene image unavailable. You can continue using the navigation.": "场景图片暂不可用，您仍可通过导航继续浏览。",
  "Panorama unavailable. Static view and product navigation remain available.": "全景暂不可用，您仍可查看静态画面及产品信息。",
  "Moving to the apartment complex": "正在前往公寓楼",
  "Moving from city to apartment": "从城市进入公寓楼",
  "loaded": "已加载",
  "Low-voltage switchgear": "低压开关柜",
  "Close product details": "关闭产品详情",
  "OVERVIEW": "概述",
  "APPLICATION GUIDE": "应用说明",
  "Independent visualization · not a configuration drawing": "独立可视化演示 · 非配置图纸",
  "Power distribution.": "配电系统。",
  "Built around your needs.": "围绕您的需求构建。",
  "This demonstration presents a modular low-voltage switchgear assembly. Separate functional units illustrate incoming supply, power distribution and motor control within a building.": "本演示展示模块化低压开关柜组合，通过不同功能单元呈现建筑内的进线、配电与电动机控制。",
  "A modular approach": "模块化设计",
  "Power distribution and motor control in one system": "在同一系统中集成配电与电动机控制",
  "Adaptable functional units and cabinet arrangements": "灵活配置功能单元与柜体布局",
  "Options for monitoring and integration": "提供监测与系统集成选项",
  "Conceptual visualization only. This is not a specified product or an engineering drawing. Equipment selection, ratings and compliance require project-specific verification.": "本内容仅为概念可视化，不代表具体产品或工程图纸。设备选型、额定参数及合规要求需按实际项目核实。",
  "Application guide": "应用说明",
  "Understand the role of each functional section in this conceptual electrical room.": "了解概念电气室中各功能分区的作用。",
  "A green city with office towers, apartments, hospital, airport and renewable energy": "包含办公楼、公寓、医院、机场与可再生能源设施的绿色城市",
  "White apartment complex with recessed windows, balconies, solar panels and EV charging": "配有内凹窗、阳台、太阳能板与电动汽车充电设施的白色公寓楼",
  "Electrical room with modular low-voltage switchgear": "配有模块化低压开关柜的电气室",
  "Independently modeled modular low-voltage switchgear assembly": "独立建模的模块化低压开关柜组合",
  "Electrical room panorama. Drag or use arrow keys to look around. Home resets the view.": "电气室全景。拖动或使用方向键环视，按 Home 键重置视角。",
  "Explore low-voltage switchgear": "探索低压开关柜",
  "Modular power distribution demonstration": "模块化配电系统演示",
  "Incoming supply": "进线单元",
  "The incoming section connects the building supply to the distribution assembly and provides a place for isolation and protection.": "进线单元连接建筑电源与配电装置，并为隔离和保护功能提供配置空间。",
  "Distribution circuits": "配电回路",
  "Outgoing sections organize power delivery to building loads. Actual protection and circuit arrangements depend on the project design.": "出线单元组织各建筑负载的电力分配，实际保护与回路配置需依据项目设计。",
  "Monitoring and operation": "监测与运行",
  "Metering and status interfaces can support operation and maintenance. This demonstration does not connect to live equipment or telemetry.": "计量与状态接口可辅助运行维护。本演示未接入真实设备或实时遥测数据。",
  "ECC is the demonstration platform identity. The cabinet models are generic illustrations, not a manufacturer's product specification.": "ECC 为演示平台名称。柜体模型是通用示意，不作为制造商产品规格。",
};
export function translate(locale: Locale, text: string): string {
  return locale === "zh" ? (zh[text] ?? text) : text;
}
