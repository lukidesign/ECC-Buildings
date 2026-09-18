export type SceneId = "city" | "apartment" | "room";
export const paths: Record<SceneId, string> = { city: "/buildings", apartment: "/buildings/bt_appart", room: "/buildings/bt_appart/bt_appart_el_room" };
export function parseLocation(pathname: string, search = ""): { scene: SceneId; product: boolean } {
  const normalized = pathname.replace(/\/+$/, "");
  const scene: SceneId = normalized === paths.room ? "room" : normalized === paths.apartment ? "apartment" : "city";
  return { scene, product: scene === "room" && ["low_voltage_switchgear", "low_voltage_mns_switchgear"].includes(new URLSearchParams(search).get("mc") ?? "") };
}
