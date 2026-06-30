import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

export interface User {
  id: number;
  email: string;
  nombres: string;
  apellidos?: string;
}

export interface Company {
  id: number;
  nombre: string;
  razon_social?: string;
  ruc?: string;
  estado: string;
}

interface AuthContextType {
  user: User | null;
  companies: Company[];
  activeCompanyId: number | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (nombres: string, email: string, password: string) => Promise<{ success: boolean; message?: string; error?: string }>;
  logout: () => Promise<void>;
  verifyEmail: (token: string) => Promise<{ success: boolean; message?: string; error?: string }>;
  resendVerification: (email: string) => Promise<{ success: boolean; message?: string; error?: string }>;
  setActiveCompany: (companyId: number) => void;
  refreshUserData: () => Promise<void>;
  showAuthModal: boolean;
  authModalTab: 'login' | 'register';
  openAuthModal: (tab?: 'login' | 'register') => void;
  closeAuthModal: () => void;
  requestPasswordReset: (email: string) => Promise<{ success: boolean; exists?: boolean; message?: string; error?: string }>;
  confirmPasswordReset: (token: string, password: string) => Promise<{ success: boolean; message?: string; error?: string }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.DEV ? 'http://127.0.0.1:8000/api/v1' : '/api/v1');

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [activeCompanyId, setActiveCompanyIdState] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authModalTab, setAuthModalTab] = useState<'login' | 'register'>('login');

  const setActiveCompany = (companyId: number) => {
    localStorage.setItem('activeCompanyId', companyId.toString());
    setActiveCompanyIdState(companyId);
  };

  const refreshUserData = async (tokenOverride?: string) => {
    const token = tokenOverride || localStorage.getItem('amazonia_access');
    if (!token) return;

    try {
      // Usar fetch directo o api axios configurando la cabecera
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      };

      const response = await fetch(`${API_URL}/companies/`, { headers });
      const rawData = await response.json();

      if (response.ok) {
        const companiesList = Array.isArray(rawData)
          ? rawData
          : (rawData && Array.isArray(rawData.results) ? rawData.results : []);
        
        setCompanies(companiesList);

        if (companiesList.length > 0) {
          const storedActiveId = localStorage.getItem('activeCompanyId');
          let currentActiveId = storedActiveId ? parseInt(storedActiveId, 10) : null;
          
          const exists = companiesList.some((c) => c.id === currentActiveId);
          if (!exists || !currentActiveId) {
            currentActiveId = companiesList[0].id;
          }
          
          localStorage.setItem('activeCompanyId', currentActiveId.toString());
          setActiveCompanyIdState(currentActiveId);
        } else {
          const storedUser = localStorage.getItem('amazonia_user');
          const parsedUser = storedUser ? JSON.parse(storedUser) : null;
          const isUserAdmin = (user?.email === 'admin') || (parsedUser?.email === 'admin');
          
          if (isUserAdmin) {
            setActiveCompanyIdState(1);
          } else {
            localStorage.removeItem('activeCompanyId');
            setActiveCompanyIdState(null);
          }
        }
      }
    } catch (error) {
      console.error("Error al cargar empresas del usuario:", error);
    }
  };

  useEffect(() => {
    const restoreSession = async () => {
      const storedUser = localStorage.getItem('amazonia_user');
      const storedToken = localStorage.getItem('amazonia_access');
      
      if (storedUser && storedToken) {
        try {
          const parsedUser = JSON.parse(storedUser);
          setUser(parsedUser);
          // Cargar empresas
          await refreshUserData(storedToken);
        } catch (e) {
          localStorage.removeItem('amazonia_user');
          localStorage.removeItem('amazonia_access');
          localStorage.removeItem('amazonia_refresh');
          localStorage.removeItem('activeCompanyId');
        }
      }
      setIsLoading(false);
    };

    restoreSession();
  }, []);

  const openAuthModal = (tab: 'login' | 'register' = 'login') => {
    setAuthModalTab(tab);
    setShowAuthModal(true);
  };

  const closeAuthModal = () => {
    setShowAuthModal(false);
  };

  const requestPasswordReset = async (email: string) => {
    try {
      const response = await fetch(`${API_URL}/auth/password-reset/request/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });
      const data = await response.json();
      if (!response.ok) {
        return { 
          success: false, 
          exists: data.exists, 
          error: data.message || (data.email ? data.email[0] : 'Error en la solicitud') 
        };
      }
      return { success: true, exists: data.exists, message: data.message };
    } catch (error) {
      console.error('Error en solicitud de recuperación:', error);
      return { success: false, error: 'Error de conexión con el servidor' };
    }
  };

  const confirmPasswordReset = async (token: string, password: string) => {
    try {
      const response = await fetch(`${API_URL}/auth/password-reset/confirm/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token, password, confirm_password: password }),
      });
      const data = await response.json();
      if (!response.ok) {
        return { 
          success: false, 
          error: data.message || (data.password ? data.password[0] : (data.token ? data.token[0] : 'Error al restablecer contraseña')) 
        };
      }
      return { success: true, message: data.message };
    } catch (error) {
      console.error('Error al confirmar recuperación:', error);
      return { success: false, error: 'Error de conexión con el servidor' };
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch(`${API_URL}/auth/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        return { success: false, error: data.detail || 'Credenciales inválidas' };
      }

      localStorage.setItem('amazonia_access', data.access);
      localStorage.setItem('amazonia_refresh', data.refresh);
      localStorage.setItem('amazonia_user', JSON.stringify(data.user));
      setUser(data.user);

      // Cargar empresas asociadas inmediatamente
      await refreshUserData(data.access);

      closeAuthModal();
      return { success: true };
    } catch (error) {
      console.error('Error en login:', error);
      return { success: false, error: 'Error de conexión con el servidor' };
    }
  };

  const register = async (nombres: string, email: string, password: string) => {
    try {
      const response = await fetch(`${API_URL}/auth/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ nombres, email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        let errorMsg = 'Error al registrar el usuario';
        if (data.email) errorMsg = data.email[0] || errorMsg;
        else if (data.password) errorMsg = data.password[0] || errorMsg;
        else if (data.detail) errorMsg = data.detail;
        else if (typeof data === 'object') {
          const keys = Object.keys(data);
          if (keys.length > 0) {
            errorMsg = data[keys[0]][0] || errorMsg;
          }
        }
        return { success: false, error: errorMsg };
      }

      return { success: true, message: data.message };
    } catch (error) {
      console.error('Error en registro:', error);
      return { success: false, error: 'Error de conexión con el servidor' };
    }
  };

  const logout = async () => {
    const access = localStorage.getItem('amazonia_access');
    const refresh = localStorage.getItem('amazonia_refresh');

    localStorage.removeItem('amazonia_access');
    localStorage.removeItem('amazonia_refresh');
    localStorage.removeItem('amazonia_user');
    localStorage.removeItem('activeCompanyId');
    setUser(null);
    setCompanies([]);
    setActiveCompanyIdState(null);

    if (access && refresh) {
      try {
        await fetch(`${API_URL}/auth/logout/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access}`,
          },
          body: JSON.stringify({ refresh }),
        });
      } catch (error) {
        console.error('Error al notificar logout al backend:', error);
      }
    }
  };

  const verifyEmail = async (token: string) => {
    try {
      const response = await fetch(`${API_URL}/auth/verify-email/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      const data = await response.json();

      if (!response.ok) {
        return { success: false, error: data.error || data.detail || 'Token inválido o expirado' };
      }

      return { success: true, message: data.message };
    } catch (error) {
      console.error('Error en verificación de correo:', error);
      return { success: false, error: 'Error de conexión con el servidor' };
    }
  };

  const resendVerification = async (email: string) => {
    try {
      const response = await fetch(`${API_URL}/auth/resend-verification/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        return { success: false, error: data.email?.[0] || data.detail || 'Error al reenviar el correo de verificación' };
      }

      return { success: true, message: data.message || 'Correo de verificación reenviado.' };
    } catch (error) {
      console.error('Error al reenviar verificación:', error);
      return { success: false, error: 'Error de conexión con el servidor' };
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        companies,
        activeCompanyId,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        verifyEmail,
        resendVerification,
        setActiveCompany,
        refreshUserData: () => refreshUserData(),
        showAuthModal,
        authModalTab,
        openAuthModal,
        closeAuthModal,
        requestPasswordReset,
        confirmPasswordReset,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe ser utilizado dentro de un AuthProvider');
  }
  return context;
};
