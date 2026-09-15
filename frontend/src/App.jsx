import { Route, Routes } from "react-router-dom";
import Layout from "./components/common/Layout";
import RequireAuth from "./components/common/RequireAuth";
import { useMapSelection } from "./hooks/useMapSelection";
import { useEnvironment } from "./hooks/useEnvironment";
import { useChat } from "./hooks/useChat";
import { useConversations } from "./hooks/useConversations";
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
 * renders outside <RequireAuth> and outside <Layout>.
 *
 * useChat/useConversations/useEnvironment all live HERE, alongside
 * useMapSelection, for the same reason: ProtectedApp only unmounts on
 * sign-out, never on navigating between routes — only the <Routes>
 * children do. Owning this state here (and passing it down as props) is
 * what makes it survive a trip to another page and back, instead of
 * resetting every time the page that used to own it unmounts. This now
 * covers: chat messages/session, the sidebar's conversation list, the
 * selected map point, AND that point's fetched environmental data — all
 * four used to live inside the page component that displayed them and
 * reset on navigation; none of them do anymore.
 */
function ProtectedApp() {
  const { selection, select, clear } = useMapSelection();
  const environment = useEnvironment();
  const chat = useChat();
  const conversations = useConversations();

  return (
    <RequireAuth>
      <Layout>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route
            path="/assistant"
            element={
              <AIAssistant
                mapSelection={selection}
                onClearMapSelection={clear}
                chat={chat}
                conversations={conversations}
              />
            }
          />
          <Route
            path="/map"
            element={<MapExplorer onSelect={select} mapSelection={selection} environment={environment} />}
          />
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