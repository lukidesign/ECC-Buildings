"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Building2, ChevronDown, ChevronRight, Home, Info, Menu, RotateCcw, X, Zap } from "lucide-react";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Panorama from "./panorama";
import { parseLocation, paths, type SceneId } from "./navigation";

import { LanguageSwitch, useLanguage } from "./language";

type Marker = { x: number; y: number };
type SceneMetadata = { markers: Record<string, Marker>; resolution: [number, number] };
const titles = { city: "Buildings", apartment: "Residential | Apartment complex", room: "Electrical Room" };
const labels = { city: "Residential | Apartment complex", apartment: "Electrical Room", room: "LV Switchgear" };
const markerKeys = { city: "apartment", apartment: "electrical-room", room: "mns" };
const steps: SceneId[] = ["city", "apartment", "room"];

export default function Landscape() {
  const { locale, selectLocale, t } = useLanguage();
  const [scene, setScene] = useState<SceneId>("city");
  const [product, setProduct] = useState(false);
  const [menu, setMenu] = useState(true);
  useEffect(() => { setMenu(scene !== "room"); }, [scene]);
  const [mobile, setMobile] = useState(false);
  const [ready, setReady] = useState(false);
  const [transition, setTransition] = useState(false);
  const [mediaError, setMediaError] = useState(false);
  const [panoramaState, setPanoramaState] = useState("loading");
  const [resetToken, setResetToken] = useState(0);
  const [metadata, setMetadata] = useState<Partial<Record<SceneId, SceneMetadata>>>({});
  const [size, setSize] = useState({ w: 1920, h: 1080 });
  const video = useRef<HTMLVideoElement>(null);
  const stage = useRef<HTMLDivElement>(null);
  const entry = useRef<HTMLButtonElement>(null);
  const mobileEntry = useRef<HTMLButtonElement>(null);
  const pendingTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const sceneRef = useRef<SceneId>("city");
  const modalOrigin = useRef<HTMLElement | null>(null);
  const transitionLive = useRef(false);
  const [notice, setNotice] = useState("");
  const stopTransition = useCallback((reason = "cancelled") => {
    clearTimeout(pendingTimer.current); setTransition(false);
    if (transitionLive.current) document.documentElement.dataset.transitionResult = reason;
    transitionLive.current = false;
  }, []);
  const readLocation = useCallback(() => {
    stopTransition();
    const value = parseLocation(window.location.pathname, window.location.search);
    sceneRef.current = value.scene;
    setScene(value.scene); setProduct(value.product); setMediaError(false);
  }, [stopTransition]);
  useEffect(() => {
    readLocation(); setReady(true);
    document.documentElement.dataset.runtime=JSON.stringify({userAgent:navigator.userAgent,pixelRatio:window.devicePixelRatio});
    const query = matchMedia("(max-width: 700px)");
    const resize = () => setMobile(query.matches);
    resize(); query.addEventListener("change", resize);
    window.addEventListener("popstate", readLocation);
    for (const id of steps) {
      fetch(`/assets/${id}-metadata.json?v=ecc-brand`).then(r => { if (!r.ok) throw Error("metadata"); return r.json(); })
        .then(data => setMetadata(old => ({ ...old, [id]: data }))).catch(() => {});
      const poster = new Image(); poster.src = `/assets/${id}.webp?v=ecc-brand`;
    }
    return () => { query.removeEventListener("change", resize); window.removeEventListener("popstate", readLocation); clearTimeout(pendingTimer.current); };
  }, [readLocation]);
  useEffect(() => {
    if (!stage.current) return;
    const observer = new ResizeObserver(([record]) => setSize({ w: record.contentRect.width, h: record.contentRect.height }));
    observer.observe(stage.current); return () => observer.disconnect();
  }, []);
  useEffect(() => { document.title = `${product ? t("Low-voltage switchgear") : t(titles[scene])} | ECC`; }, [scene, product, t]);
  const navigate = useCallback((target: SceneId, animate = false) => {
    stopTransition(); setProduct(false); setMediaError(false); setNotice("");
    const from = sceneRef.current;
    if (target === from) return;
    window.history.pushState({}, "", paths[target]);
    sceneRef.current = target; setScene(target);
    if (animate && from === "city" && target === "apartment" && !mobile && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
      transitionLive.current = true; document.documentElement.dataset.transitionResult = "started";
      setTransition(true); pendingTimer.current = setTimeout(() => stopTransition("timeout"), 4500);
    }
  }, [mobile, stopTransition]);
  useEffect(() => { if (transition) video.current?.play().catch(() => stopTransition("autoplay-denied")); }, [transition, stopTransition]);
  const showProduct = () => {
    if (transition) return;
    modalOrigin.current = document.activeElement as HTMLElement;
    window.history.pushState({ productEntry: true }, "", paths.room + "?mc=low_voltage_switchgear"); setProduct(true);
  };
  const closeProduct = () => {
    if (window.history.state?.productEntry) window.history.back();
    else { window.history.replaceState({}, "", paths.room); setProduct(false); }
  };
  const activate = () => scene === "room" ? showProduct() : navigate(scene === "city" ? "apartment" : "room", scene === "city");
  const back = () => { stopTransition(); navigate(scene === "room" ? "apartment" : "city"); };
  const mark = metadata[scene]?.markers[markerKeys[scene]];
  const scale = Math.max(size.w / 1920, size.h / 1080);
  const hotspotStyle = mark ? { left: (size.w - 1920 * scale) / 2 + mark.x * 1920 * scale, top: (size.h - 1080 * scale) / 2 + mark.y * 1080 * scale } : undefined;
  return <main className={`explorer ${mobile ? "is-mobile" : ""}`} data-scene={scene} aria-busy={transition}>
    {(mobile || scene === "room") && <h1 className="sr-only">{t(titles[scene])}</h1>}
    <div className="scene-stage" ref={stage}>
      <img key={scene} className="scene-image" src={`/assets/${scene}.webp?v=ecc-brand`} alt={scene === "city" ? t("A green city with office towers, apartments, hospital, airport and renewable energy") : scene === "apartment" ? t("White apartment complex with recessed windows, balconies, solar panels and EV charging") : t("Electrical room with modular low-voltage switchgear")} onError={() => setMediaError(true)} />
      {ready && scene === "room" && !mobile && <Panorama t={t} resetToken={resetToken} blocked={product} onStatus={setPanoramaState} onProduct={showProduct} />}
      {transition && <video ref={video} className="scene-transition" src="/assets/city-to-apartment.mp4?v=ecc-brand" poster="/assets/city.webp?v=ecc-brand" muted playsInline preload="auto" onPlaying={() => { document.documentElement.dataset.transitionResult="playing"; }} onEnded={() => stopTransition("completed")} onError={() => stopTransition("media-error")} aria-label={t("Moving from city to apartment")} />}
      {!mobile && !transition && scene !== "room" && mark && <button className="scene-hotspot" style={hotspotStyle} onClick={activate} aria-label={`${t("Explore")} ${t(labels[scene])}`}><span className="beacon"/><span className="hotspot-label"><ArrowRight size={14}/>{t(labels[scene])}</span></button>}
      {!mobile && scene === "room" && panoramaState !== "ready" && <button className="scene-hotspot" style={hotspotStyle || { left: "64%", top: "60%" }} onClick={showProduct}><span className="beacon"/><span className="hotspot-label">{t("LV Switchgear")}</span></button>}
    </div>
    <header className="scene-header">
      <nav aria-label={t("Breadcrumb")} className="breadcrumbs"><button onClick={() => navigate("city")} aria-label={t("Buildings overview")}><Home size={15} fill="currentColor"/><span className="brand-wordmark">ECC</span><span>{t("Buildings")}</span></button>{scene !== "city" && <><ChevronRight size={14}/><button onClick={() => navigate("apartment")} aria-current={scene === "apartment" ? "page" : undefined}>{t("Residential | Apartment complex")}</button></>}{scene === "room" && <><ChevronRight size={14}/><span aria-current="page">{t("Electrical Room")}</span></>}</nav>
      {scene !== "room" && <div className="heading-row"><button className="icon-button" aria-label={menu ? t("Hide navigation") : t("Show navigation")} aria-expanded={menu} onClick={() => setMenu(!menu)}><Menu size={23}/></button><h1><span/>{t(titles[scene])}</h1></div>}
    </header>
    <div className="top-actions"><div className="top-note"><span className="status-dot"/>{t("ECC · Spatial Explorer")}</div><LanguageSwitch locale={locale} onChange={selectLocale}/></div>
    <aside className={`navigation-card ${menu ? "" : "collapsed"}`}><button className="card-heading" aria-expanded={menu} onClick={() => setMenu(!menu)}><Building2 size={21}/><span>{scene === "city" ? t("Explore buildings") : t("Building Applications")}</span><ChevronDown size={14}/></button>{menu && <div className="card-content">{scene === "city" ? <><p className="context-copy">{t("Discover connected spaces.")}<br/>{t("Start with the apartment complex.")}</p><button className="destination active" onClick={() => navigate("apartment", true)}><Building2 size={23}/><span>{t("Residential")}<br/><strong>{t("Apartment complex")}</strong></span><ArrowRight size={17}/></button><p className="scope-note">{t("One building. A complete journey.")}</p></> : <><div className="application"><Zap size={25}/><span>{t("Power Distribution")}</span></div><p className="context-copy">{scene === "apartment" ? t("Explore the electrical systems behind a connected residential building.") : t("Reliable power, from the incoming supply to every connected space.")}</p><div className="divider"/><button ref={entry} className="destination" onClick={activate}><span>{scene === "apartment" ? t("Electrical Room") : t("Modular LV switchgear")}</span><ArrowRight size={17}/></button></>}</div>}</aside>
    <section className="mobile-guide" aria-label={t("Scene navigation")}><span className="eyebrow">{scene === "city" ? t("01 / THE CITY") : scene === "apartment" ? t("02 / THE BUILDING") : t("03 / THE ELECTRICAL ROOM")}</span><h2>{t(titles[scene])}</h2><p>{scene === "city" ? t("Explore a connected city, one building at a time.") : scene === "apartment" ? t("Step inside the systems that bring a residential building to life.") : t("Discover modular power distribution inside the electrical room.")}</p><button ref={mobileEntry} className="mobile-entry" onClick={activate}>{t(labels[scene])}<ArrowRight size={18}/></button></section>
    <div className="bottom-controls">{scene !== "city" && <button className="back-control" onClick={back}><img src={`/assets/${scene === "room" ? "apartment" : "city"}.webp?v=ecc-brand`} alt=""/><span><ArrowLeft size={16}/>{t("BACK")}</span></button>}</div>
    {scene === "room" && !mobile && <div className="room-controls"><span>{t("Drag to look around · Arrow keys to rotate")}</span><button aria-label={t("Reset room view")} onClick={() => { setResetToken(v => v + 1); setNotice("Room view reset"); }}><RotateCcw size={18}/></button></div>}
    {scene === "city" && <p className="city-instruction"><span className="beacon small"/>{t("Select a building to explore")}</p>}
    <footer className="scene-footer">{t("ECC Spatial Explorer")}<span>·</span>{t("Independently modeled study")}<span>·</span>{t("Interactive demonstration")}</footer>
    {(mediaError || (scene === "room" && panoramaState === "error" && !mobile)) && <div role="status" className="fallback-notice"><Info size={16}/> {mediaError ? t("Scene image unavailable. You can continue using the navigation.") : t("Panorama unavailable. Static view and product navigation remain available.")}</div>}
    <div className="sr-only" role="status" aria-live="polite">{(notice ? t(notice) : "") || (transition ? t("Moving to the apartment complex") : `${t(titles[scene])} ${t("loaded")}`)}</div>
    <Sheet open={product} onOpenChange={value => { if (!value) closeProduct(); }}><SheetContent className="product-sheet" showCloseButton={false} onCloseAutoFocus={event => { event.preventDefault(); (modalOrigin.current?.isConnected ? modalOrigin.current : mobile ? mobileEntry.current : entry.current)?.focus(); }}>
      <SheetHeader className="product-header"><div className="product-language"><LanguageSwitch locale={locale} onChange={selectLocale}/></div><span className="brand-rule"/><span className="product-brand">ECC</span><SheetTitle>{t("Low-voltage switchgear")}</SheetTitle><SheetDescription>{t("Modular power distribution demonstration")}</SheetDescription><button className="product-close" aria-label={t("Close product details")} onClick={closeProduct}><X size={22}/></button></SheetHeader>
      <Tabs defaultValue="overview" className="product-tabs"><TabsList variant="line" className="product-tablist"><TabsTrigger value="overview">{t("OVERVIEW")}</TabsTrigger><TabsTrigger value="guide">{t("APPLICATION GUIDE")}</TabsTrigger></TabsList><TabsContent value="overview" className="product-content"><img className="product-image" src="/assets/product.webp" alt={t("Independently modeled modular low-voltage switchgear assembly")}/><span className="image-caption">{t("Independent visualization · not a configuration drawing")}</span><h2>{t("Power distribution.")}<br/>{t("Built around your needs.")}</h2><p>{t("This demonstration presents a modular low-voltage switchgear assembly. Separate functional units illustrate incoming supply, power distribution and motor control within a building.")}</p><h3>{t("A modular approach")}</h3><ul><li>{t("Power distribution and motor control in one system")}</li><li>{t("Adaptable functional units and cabinet arrangements")}</li><li>{t("Options for monitoring and integration")}</li></ul><p className="technical-note">{t("Conceptual visualization only. This is not a specified product or an engineering drawing. Equipment selection, ratings and compliance require project-specific verification.")}</p></TabsContent><TabsContent value="guide" className="product-content guide-content">
        <h2>{t("Application guide")}</h2>
        <p>{t("Understand the role of each functional section in this conceptual electrical room.")}</p>
        <section className="guide-section"><h3>{t("Incoming supply")}</h3><p>{t("The incoming section connects the building supply to the distribution assembly and provides a place for isolation and protection.")}</p></section>
        <section className="guide-section"><h3>{t("Distribution circuits")}</h3><p>{t("Outgoing sections organize power delivery to building loads. Actual protection and circuit arrangements depend on the project design.")}</p></section>
        <section className="guide-section"><h3>{t("Monitoring and operation")}</h3><p>{t("Metering and status interfaces can support operation and maintenance. This demonstration does not connect to live equipment or telemetry.")}</p></section>
        <div className="technical-note">{t("ECC is the demonstration platform identity. The cabinet models are generic illustrations, not a manufacturer's product specification.")}</div>
      </TabsContent></Tabs>
    </SheetContent></Sheet>
  </main>;
}
