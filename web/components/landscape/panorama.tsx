"use client";
import { useEffect, useRef } from "react";
import { ArrowRight } from "lucide-react";
import roomView from "./room-view.json";
const baseFov = 2 * Math.atan(roomView.sensorWidthMm / roomView.baseAspect / (2 * roomView.lensMm)) * 180 / Math.PI;
type Props = { t: (text: string) => string; resetToken: number; blocked: boolean; onStatus: (status: string) => void; onProduct: () => void };
export default function Panorama({ t, resetToken, blocked, onStatus, onProduct }: Props) {
  const host = useRef<HTMLDivElement>(null), hotspot = useRef<HTMLButtonElement>(null);
  const orientation = useRef({ yaw: 0, pitch: 0 }), renderNow = useRef<() => void>(() => {});
  const blockedRef = useRef(blocked), statusRef = useRef(onStatus);
  const tap = useRef({ x:0, y:0, moved:false });
  blockedRef.current = blocked; statusRef.current = onStatus;
  useEffect(() => { orientation.current = { yaw: 0, pitch: 0 }; renderNow.current(); }, [resetToken]);
  useEffect(() => {
    const target = host.current;
    if (!target) return;
    let disposed = false, teardown = () => {};
    const startedAt = performance.now();
    statusRef.current("loading");
    import("three").then(THREE => {
      if (disposed) return;
      let renderer: import("three").WebGLRenderer;
      try { renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); }
      catch { statusRef.current("error"); return; }
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); renderer.outputColorSpace = THREE.SRGBColorSpace;
      target.appendChild(renderer.domElement);
      const world = new THREE.Scene(), camera = new THREE.PerspectiveCamera(baseFov, roomView.baseAspect, .01, 100);
      const geometry = new THREE.SphereGeometry(10, 96, 64); geometry.scale(-1, 1, 1); geometry.rotateY(-Math.PI / 2);
      const material = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0 }); world.add(new THREE.Mesh(geometry, material));
      // Same source contract as Blender; Blender +Y becomes panorama -Z.
      const marker = new THREE.Vector3(roomView.hotspot[0]-roomView.eye[0], roomView.hotspot[2]-roomView.eye[2], -(roomView.hotspot[1]-roomView.eye[1]));
      let texture: import("three").Texture | null = null, loaded = false;
      const draw = () => {
        if (disposed) return;
        const { yaw, pitch } = orientation.current; camera.rotation.set(pitch, yaw, 0, "YXZ"); camera.updateMatrixWorld(); renderer.render(world, camera);
        if (hotspot.current) {
          const p = marker.clone().project(camera), visible = loaded && p.z < 1 && p.z > -1 && Math.abs(p.x) < .90 && Math.abs(p.y) < .86;
          hotspot.current.style.visibility = visible ? "visible" : "hidden";
          hotspot.current.style.left = `${(p.x * .5 + .5) * target.clientWidth}px`; hotspot.current.style.top = `${(-p.y * .5 + .5) * target.clientHeight}px`; hotspot.current.tabIndex = visible ? 0 : -1;
        }
        target.dataset.yaw = String(Math.round(yaw * 1000) / 1000); target.dataset.pitch = String(Math.round(pitch * 1000) / 1000);
        target.dataset.viewRevision = roomView.revision;
        target.dataset.renderInfo = JSON.stringify({viewport:[target.clientWidth,target.clientHeight],nativePixelRatio:window.devicePixelRatio,pixelRatio:renderer.getPixelRatio(),drawingBuffer:[renderer.domElement.width,renderer.domElement.height],postProcessingBuffer:null,fov:camera.fov,eye:roomView.eye,benchmark:false});
      };
      renderNow.current = draw;
      const resize = () => {
        camera.aspect = target.clientWidth / Math.max(1, target.clientHeight);
        // Preserve the entire cabinet row when the viewport is wider OR narrower.
        camera.fov = 2 * Math.atan(Math.tan(baseFov * Math.PI / 360) * roomView.baseAspect / camera.aspect) * 180 / Math.PI;
        camera.updateProjectionMatrix(); renderer.setSize(target.clientWidth, target.clientHeight); draw();
      };
      const observer = new ResizeObserver(resize); observer.observe(target); resize();
      new THREE.TextureLoader().load("/assets/room-panorama.webp?v=ecc-brand", image => {
        if (disposed) { image.dispose(); return; }
        texture = image; image.colorSpace = THREE.SRGBColorSpace; image.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
        material.map = image; material.opacity = 1; material.needsUpdate = true; loaded = true; draw(); target.dataset.readyMs=String(Math.round(performance.now()-startedAt)); statusRef.current("ready");
      }, undefined, () => { if (!disposed) statusRef.current("error"); });
      let drag: { id: number; x: number; y: number; yaw: number; pitch: number; moved: boolean } | null = null;
      const down = (event: PointerEvent) => {
        if (blockedRef.current || event.button !== 0 || (event.target as HTMLElement).closest("button")) return;
        drag = { id: event.pointerId, x: event.clientX, y: event.clientY, ...orientation.current, moved: false }; target.setPointerCapture(event.pointerId); target.focus();
      };
      const move = (event: PointerEvent) => {
        if (!drag || event.pointerId !== drag.id || blockedRef.current) return;
        const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
        if (Math.hypot(dx, dy) > 5) drag.moved = true;
        if (!drag.moved) return;
        orientation.current = { yaw: drag.yaw + dx * .003, pitch: Math.max(-.72, Math.min(.72, drag.pitch + dy * .0025)) }; draw();
      };
      const up = (event: PointerEvent) => { if (drag?.id === event.pointerId) { if (target.hasPointerCapture(event.pointerId)) target.releasePointerCapture(event.pointerId); drag = null; } };
      const keyboard = (event: KeyboardEvent) => {
        if (blockedRef.current || event.target !== target || !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home"].includes(event.key)) return;
        event.preventDefault(); const current = orientation.current;
        if (event.key === "Home") { current.yaw = 0; current.pitch = 0; }
        if (event.key === "ArrowLeft") current.yaw += .12;
        if (event.key === "ArrowRight") current.yaw -= .12;
        if (event.key === "ArrowUp") current.pitch = Math.min(.72, current.pitch + .08);
        if (event.key === "ArrowDown") current.pitch = Math.max(-.72, current.pitch - .08);
        draw();
      };
      const lost = (event: Event) => { event.preventDefault(); loaded = false; if (hotspot.current) hotspot.current.style.visibility = "hidden"; renderer.domElement.style.opacity = "0"; statusRef.current("error"); };
      const restored = () => { renderer.domElement.style.opacity = "1"; loaded = !!texture; draw(); statusRef.current(loaded ? "ready" : "loading"); };
      target.addEventListener("pointerdown", down); target.addEventListener("pointermove", move); target.addEventListener("pointerup", up); target.addEventListener("pointercancel", up); target.addEventListener("keydown", keyboard);
      renderer.domElement.addEventListener("webglcontextlost", lost); renderer.domElement.addEventListener("webglcontextrestored", restored);
      teardown = () => {
        observer.disconnect(); target.removeEventListener("pointerdown", down); target.removeEventListener("pointermove", move); target.removeEventListener("pointerup", up); target.removeEventListener("pointercancel", up); target.removeEventListener("keydown", keyboard);
        renderer.domElement.removeEventListener("webglcontextlost", lost); renderer.domElement.removeEventListener("webglcontextrestored", restored);
        texture?.dispose(); geometry.dispose(); material.dispose(); renderer.dispose(); renderer.domElement.remove();
      };
    }).catch(() => { if (!disposed) statusRef.current("error"); });
    return () => { disposed = true; renderNow.current = () => {}; teardown(); };
  }, []);
  return <div className="panorama" ref={host} tabIndex={0} role="region" aria-label={t("Electrical room panorama. Drag or use arrow keys to look around. Home resets the view.")}><button ref={hotspot} className="scene-hotspot panorama-hotspot" style={{ visibility: "hidden" }} onPointerDown={e => { tap.current={x:e.clientX,y:e.clientY,moved:false}; }} onPointerMove={e => { if(Math.hypot(e.clientX-tap.current.x,e.clientY-tap.current.y)>5) tap.current.moved=true; }} onClick={e => { if(e.detail===0 || !tap.current.moved) onProduct(); }} aria-label={t("Explore low-voltage switchgear")}><span className="beacon"/><span className="hotspot-label"><ArrowRight size={14}/>{t("LV Switchgear")}</span></button></div>;
}
