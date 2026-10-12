import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import AgenciesPage from "./pages/AgenciesPage";
import AssetDetailPage from "./pages/AssetDetailPage";
import DashboardPage from "./pages/DashboardPage";
import DiscoveryPage from "./pages/DiscoveryPage";
import LoginPage from "./pages/LoginPage";
import RoutersPage from "./pages/RoutersPage";
import SnmpProfilesPage from "./pages/SnmpProfilesPage";
import SubnetsPage from "./pages/SubnetsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/assets/:id"
        element={
          <ProtectedRoute>
            <AssetDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/agencies"
        element={
          <ProtectedRoute>
            <AgenciesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/subnets"
        element={
          <ProtectedRoute>
            <SubnetsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/routers"
        element={
          <ProtectedRoute>
            <RoutersPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/snmp-profiles"
        element={
          <ProtectedRoute>
            <SnmpProfilesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/discovery"
        element={
          <ProtectedRoute>
            <DiscoveryPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}