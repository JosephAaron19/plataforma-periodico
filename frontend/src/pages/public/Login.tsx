import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { BookOpen, Mail, Lock, ArrowRight, AlertCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Flujo de Autologin Single Sign-On (SSO) local
  React.useEffect(() => {
    const params = new URLSearchParams(location.search);
    const ssoToken = params.get('sso_token');
    const ssoUserRaw = params.get('sso_user');
    const redirectPath = params.get('redirect') || '/dashboard';

    if (ssoToken && ssoUserRaw) {
      setIsLoading(true);
      setError('');
      try {
        const ssoUser = JSON.parse(decodeURIComponent(ssoUserRaw));
        
        // Almacenar el token en localStorage temporalmente para el cliente API
        localStorage.setItem('token', ssoToken);

        const performSSOLogin = async () => {
          let userCompanies = [];
          try {
            const companiesResponse = await api.get('/companies/');
            const rawData = companiesResponse.data;
            userCompanies = Array.isArray(rawData)
              ? rawData
              : (rawData && Array.isArray(rawData.results) ? rawData.results : []);
          } catch (compErr) {
            console.warn("No se pudieron cargar las empresas asociadas al usuario durante SSO:", compErr);
          }

          // Iniciar sesión en el contexto global
          login(ssoToken, ssoUser, userCompanies);
          
          // Redirigir al path correspondiente (dashboard o subruta)
          navigate(redirectPath, { replace: true });
        };

        performSSOLogin();
      } catch (err) {
        console.error("Error al procesar los datos de SSO:", err);
        setError('Error al iniciar sesión automáticamente. Por favor ingresa manualmente.');
        setIsLoading(false);
      }
    }
  }, [location, login, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // Endpoint POST /api/auth/login
      const response = await api.post('/auth/login/', { email, password });
      const { access, user } = response.data;
      
      // Store token temporarily so we can perform authenticated requests
      localStorage.setItem('token', access);

      // Fetch user's companies from /api/v1/companies/
      let userCompanies = [];
      try {
        const companiesResponse = await api.get('/companies/');
        const rawData = companiesResponse.data;
        userCompanies = Array.isArray(rawData)
          ? rawData
          : (rawData && Array.isArray(rawData.results) ? rawData.results : []);
      } catch (compErr) {
        console.warn("No se pudieron cargar las empresas asociadas al usuario:", compErr);
      }

      login(access, user, userCompanies);

      // Redirect to dashboard for admin user, otherwise redirect to landing page
      if (email.trim().toLowerCase() === 'admin' || user.email === 'admin') {
        navigate('/dashboard', { replace: true });
      } else {
        navigate('/', { replace: true });
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        err.response?.data?.error || 
        'Credenciales inválidas. Por favor intenta nuevamente.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link to="/" className="flex justify-center items-center gap-2 mb-6">
          <BookOpen className="h-10 w-10 text-brand-600" />
          <span className="text-2xl font-bold text-gray-900">DigitalSaaS</span>
        </Link>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Inicia sesión en tu cuenta
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          ¿O eres nuevo?{' '}
          <Link to="/register" className="font-medium text-brand-600 hover:text-brand-500 transition-colors">
            Crea tu cuenta gratis
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-2xl sm:px-10 border border-gray-100">
          
          {location.state?.message && (
            <div className="mb-4 bg-green-50 border-l-4 border-green-500 p-4 rounded-md flex items-start">
              <AlertCircle className="h-5 w-5 text-green-600 mr-3 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-700">{location.state.message}</p>
            </div>
          )}

          {error && (
            <div className="mb-4 bg-red-50 border-l-4 border-red-500 p-4 rounded-md flex items-start">
              <AlertCircle className="h-5 w-5 text-red-500 mr-3 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Correo Electrónico
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="text"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-10 sm:text-sm border-gray-300 rounded-lg focus:ring-brand-500 focus:border-brand-500 py-3 bg-gray-50 border"
                  placeholder="tu@correo.com o usuario"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Contraseña
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 sm:text-sm border-gray-300 rounded-lg focus:ring-brand-500 focus:border-brand-500 py-3 bg-gray-50 border"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 transition-colors disabled:opacity-70"
              >
                {isLoading ? 'Iniciando sesión...' : 'Entrar al Dashboard'}
                {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
