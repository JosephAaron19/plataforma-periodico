export interface User {
  id: number;
  email: string;
  nombre?: string;
  is_active: boolean;
}

export interface Company {
  id: number;
  nombre: string;
  nombre_comercial?: string;
  pais: string;
  tipo_negocio: string;
  role: string; // The user's role in this company
}

export interface AuthState {
  user: User | null;
  companies: Company[];
  activeCompanyId: number | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
