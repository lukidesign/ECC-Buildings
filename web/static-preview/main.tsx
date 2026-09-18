import { createRoot } from "react-dom/client";
import Landscape from "../components/landscape/landscape";
import "../app/globals.css";
import "../app/explorer.css";

const root = document.getElementById("root");
if (!root) throw new Error("ECC Buildings root element is missing.");
createRoot(root).render(<Landscape />);
