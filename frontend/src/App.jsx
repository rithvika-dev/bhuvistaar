import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/layout/Layout";

import Login from "./pages/Login";
import Register from "./pages/Register";

import Dashboard from "./pages/Dashboard";
import DataIngestion from "./pages/DataIngestion";
import Datasets from "./pages/Datasets";
import Harmonization from "./pages/Harmonization";
import Conflicts from "./pages/Conflicts";
import Verification from "./pages/Verification";
import VerifiedRecords from "./pages/VerifiedRecords";
import GISMap from "./pages/GISMap";
import ChangeDetection from "./pages/ChangeDetection";
import TopologyValidation from "./pages/TopologyValidation";
import Reports from "./pages/Reports";
import AuditTrail from "./pages/AuditTrail";
import Settings from "./pages/Settings";

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public auth routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected application routes */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/ingestion" element={<DataIngestion />} />
                  <Route path="/datasets" element={<Datasets />} />
                  <Route path="/harmonization" element={<Harmonization />} />
                  <Route path="/topology" element={<TopologyValidation />} />
                  <Route path="/map" element={<GISMap />} />
                  <Route path="/conflicts" element={<Conflicts />} />
                  <Route path="/changes" element={<ChangeDetection />} />
                  <Route path="/review" element={<Verification />} />
                  <Route path="/verified" element={<VerifiedRecords />} />
                  <Route path="/reports" element={<Reports />} />
                  <Route path="/audit" element={<AuditTrail />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </AuthProvider>
  );
}

export default App;