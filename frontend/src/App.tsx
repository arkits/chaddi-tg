import { Routes, Route } from "react-router-dom";
import Layout from "./components/layout/layout";
import Dashboard from "./pages/dashboard";
import Bakchods from "./pages/bakchods";
import BakchodDetail from "./pages/bakchod-detail";
import Groups from "./pages/groups";
import GroupDetail from "./pages/group-detail";
import Quotes from "./pages/quotes";
import Jobs from "./pages/jobs";
import Commands from "./pages/commands";
import Logs from "./pages/logs";
import Messenger from "./pages/messenger";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="bakchods" element={<Bakchods />} />
        <Route path="bakchods/:tgId" element={<BakchodDetail />} />
        <Route path="groups" element={<Groups />} />
        <Route path="groups/:groupId" element={<GroupDetail />} />
        <Route path="quotes" element={<Quotes />} />
        <Route path="jobs" element={<Jobs />} />
        <Route path="commands" element={<Commands />} />
        <Route path="logs" element={<Logs />} />
        <Route path="messenger" element={<Messenger />} />
      </Route>
    </Routes>
  );
}
