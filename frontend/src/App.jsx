import { Route, Routes } from "react-router-dom";
import Layout from "./components/common/Layout";
import RequireAuth from "./components/common/RequireAuth";
import { useMapSelection } from "./hooks/useMapSelection";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import AIAssistant from "./pages/AIAssistant";
import MapExplorer from "./pages/MapExplorer";
import TreeSpecies from "./pages/TreeSpecies";
import SpeciesDetailPage from "./pages/SpeciesDetailPage";
import KnowledgeSources from "./pages/KnowledgeSources";
import About from "./pages/About";

/**
 * The whole app requires sign-in (chat history is tied to the user's
 * Google-authenticated account) — so `/login` is the ONLY route that
 * renders outside <RequireAuth> and outside <Layout>. It needs to be
 * full-bleed (no nav bar) for its split-screen illustration to work, and
 * it obviously can't itself be behind the auth gate it's providing.
 *
 * Every other route — including "/" and "/about", which used to be
 * reachable without signing in — now sits behind one shared
 * <RequireAuth><Layout>...</Layout></RequireAuth> wrapper via a single
 * "/*" parent route rendering a nested <Routes>, instead of repeating
 * <RequireAuth> on each route individually. This is what actually makes
 * "sign in before you see the app" true: previously, only some routes
 * were gated, so the app was reachable without authenticating at all via
 * "/" or "/about".
 */
function ProtectedApp() {
  const { selection, select, clear } = useMapSelection();

  return (
    <RequireAuth>
      <Layout>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route
            path="/assistant"
            element={<AIAssistant mapSelection={selection} onClearMapSelection={clear} />}
          />
          <Route path="/map" element={<MapExplorer onSelect={select} />} />
          <Route path="/species" element={<TreeSpecies />} />
          <Route path="/species/:id" element={<SpeciesDetailPage />} />
          <Route path="/sources" element={<KnowledgeSources />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </Layout>
    </RequireAuth>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={<ProtectedApp />} />
    </Routes>
  );
}