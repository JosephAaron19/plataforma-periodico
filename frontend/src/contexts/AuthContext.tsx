import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, Company, AuthState } from '../types/auth';
import api from '../services/api';

interface AuthContextType extends AuthState {
  login: (token: string, user: User, companies: Company[]) => void;
  logout: () => void;
  setActiveCompany: (companyId: number) => void;
  refreshUserData: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: (() => {
      const stored = localStorage.getItem('user');
      try {
        return stored ? JSON.parse(stored) : null;
      } catch {
        return null;
      }
    })(),
    companies: [],
    activeCompanyId: (() => {
      const stored = localStorage.getItem('activeCompanyId');
      return stored ? parseInt(stored, 10) : null;
    })(),
    token: localStorage.getItem('token'),
    isAuthenticated: false,
    isLoading: true,
  });

  // Function to save state and update localStorage
  const login = (token: string, user: User, companies: Company[]) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    
    // Auto-select first company if available
    let defaultCompanyId = null;
    if (companies && companies.length > 0) {
      defaultCompanyId = companies[0].id;
      localStorage.setItem('activeCompanyId', defaultCompanyId.toString());
    } else {
      localStorage.removeItem('activeCompanyId');
    }

    setState({
      user,
      companies,
      activeCompanyId: defaultCompanyId,
      token,
      isAuthenticated: true,
      isLoading: false,
    });
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('activeCompanyId');
    setState({
      user: null,
      companies: [],
      activeCompanyId: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
  };

  const setActiveCompany = (companyId: number) => {
    localStorage.setItem('activeCompanyId', companyId.toString());
    setState((prev) => ({ ...prev, activeCompanyId: companyId }));
  };

  const refreshUserData = async () => {
    try {
      const response = await api.get('/companies/');
      const rawData = response.data;
      const companies = Array.isArray(rawData)
        ? rawData
        : (rawData && Array.isArray(rawData.results) ? rawData.results : []);
      
      let currentCompanyId = state.activeCompanyId;
      if (!currentCompanyId) {
        const storedActiveId = localStorage.getItem('activeCompanyId');
        if (storedActiveId) {
          currentCompanyId = parseInt(storedActiveId, 10);
        }
      }
      
      // If the current active company ID is not in the list, fallback to the first company.
      if (companies.length > 0) {
        const exists = companies.some((c: any) => c.id === currentCompanyId);
        if (!exists) {
          currentCompanyId = companies[0].id;
        }
      } else {
        currentCompanyId = null;
      }

      if (currentCompanyId !== null) {
        localStorage.setItem('activeCompanyId', currentCompanyId.toString());
      } else {
        localStorage.removeItem('activeCompanyId');
      }

      setState((prev) => ({
        ...prev,
        companies,
        activeCompanyId: currentCompanyId,
        isAuthenticated: true,
        isLoading: false,
      }));
    } catch (error) {
      // If token is invalid or request fails, logout
      logout();
    }
  };

  // On mount, if we have a token, we should verify it and load user data
  useEffect(() => {
    const initializeAuth = async () => {
      if (state.token) {
        await refreshUserData();
      } else {
        setState((prev) => ({ ...prev, isLoading: false }));
      }
    };
    initializeAuth();
  }, [state.token]);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, setActiveCompany, refreshUserData }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
