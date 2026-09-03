import { Route, Routes } from "react-router-dom";
import Layout from "./components/common/Layout";
import { useMapSelection } from "./hooks/useMapSelection";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import AIAssistant from "./pages/AIAssistant";
import MapExplorer from "./pages/MapExplorer";
import TreeSpecies from "./pages/TreeSpecies";
import SpeciesDetailPage from "./pages/SpeciesDetailPage";
import KnowledgeSources from "./pages/KnowledgeSources";
import About from "./pages/About";

export default function App() {
  const { selection, select, clear } = useMapSelection();

  return (
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
  );
}
