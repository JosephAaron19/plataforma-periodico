import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { SimulationProvider } from './contexts/SimulationContext';

// Layouts & Guards
import PublicLayout from './components/layout/PublicLayout';
import DashboardLayout from './components/layout/DashboardLayout';
import { RequireAuth, RequireCompany } from './components/layout/Guards';

// Pages (Stubs/Imports)
// Public
import Landing from './pages/public/Landing';
import Login from './pages/public/Login';
import Register from './pages/public/Register';
import VerifyEmail from './pages/public/VerifyEmail';
import EditionDetail from './pages/public/EditionDetail';
// Onboarding
import CreateCompany from './pages/onboarding/CreateCompany';
import SelectPlan from './pages/onboarding/SelectPlan';
// Dashboard
import DashboardOverview from './pages/dashboard/DashboardOverview';
import Editions from './pages/dashboard/Editions';
import Viewer from './pages/dashboard/Viewer';

function App() {
  return (
    <AuthProvider>
      <SimulationProvider>
        <Router>
        <Routes>
          {/* Public Routes */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/verify-email" element={<VerifyEmail />} />
            <Route path="/editions/:id" element={<EditionDetail />} />
          </Route>

          {/* Protected Routes (Needs Auth, but maybe no company yet) */}
          <Route element={<RequireAuth />}>
            {/* Onboarding */}
            <Route path="/onboarding/create-company" element={<CreateCompany />} />
            <Route path="/onboarding/select-plan" element={<SelectPlan />} />

            {/* Dashboard Routes (Needs Auth AND active Company) */}
            <Route element={<RequireCompany />}>
              <Route path="/dashboard" element={<DashboardLayout />}>
                <Route index element={<DashboardOverview />} />
                <Route path="editions" element={<Editions />} />
                <Route path="viewer" element={<Viewer />} />
                <Route path="purchases" element={<div className="p-4">Compras y Pagos</div>} />
                <Route path="users" element={<div className="p-4">Gestión de Usuarios</div>} />
                <Route path="plans" element={<div className="p-4">Planes y Límites</div>} />
                <Route path="settings" element={<div className="p-4">Configuración</div>} />
              </Route>
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
      </SimulationProvider>
    </AuthProvider>
  );
}

export default App;
