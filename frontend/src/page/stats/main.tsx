import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "../../styles/tokens.css";
import "../../styles/base.css";
import "../../styles/animations.css";
import { StatsPage } from "./StatsPage";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <StatsPage />
  </StrictMode>,
);
