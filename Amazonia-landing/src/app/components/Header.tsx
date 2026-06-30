import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/auth';
import { Facebook, Mail, LogOut, User as UserIcon, ChevronDown, UserCheck } from 'lucide-react';
import logoAmazonia from '../../imports/logo_amazonia.png';
import { useNavigate } from 'react-router-dom';

export function Header() {
  const { user, isAuthenticated, logout, openAuthModal } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Cerrar el dropdown si se hace clic fuera de él
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogout = async () => {
    setDropdownOpen(false);
    await logout();
  };

  const handlePortalRedirect = (e: React.MouseEvent, targetPath: string) => {
    e.preventDefault();
    setDropdownOpen(false);
    navigate(targetPath);
  };

  // Obtener iniciales para el avatar
  const getInitials = (name: string) => {
    if (!name) return 'U';
    const parts = name.split(' ');
    if (parts.length > 1) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name[0].toUpperCase();
  };

  return (
    <header className="bg-white py-4 px-6 flex items-center justify-between shadow-sm relative z-40 border-b border-slate-100">
      {/* Logo */}
      <a href="#" className="flex items-center hover:opacity-90 transition-opacity">
        <img src={logoAmazonia} alt="Amazonia Diario" className="h-9 w-auto" />
      </a>

      {/* Menú derecho */}
      <div className="flex items-center gap-6">
        {/* Social Icons (Ocultos en móviles pequeños para priorizar auth) */}
        <div className="hidden sm:flex items-center gap-3">
          <a href="#" className="w-8 h-8 rounded-full bg-gray-50 flex items-center justify-center hover:bg-slate-100 text-slate-500 hover:text-[#1a4d2e] transition-colors">
            <Facebook size={16} />
          </a>
          <a href="#" className="w-8 h-8 rounded-full bg-gray-50 flex items-center justify-center hover:bg-slate-100 text-slate-500 hover:text-[#1a4d2e] transition-colors">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
            </svg>
          </a>
          <a href="mailto:contacto@amazoniadiario.com" className="w-8 h-8 rounded-full bg-gray-50 flex items-center justify-center hover:bg-slate-100 text-slate-500 hover:text-[#1a4d2e] transition-colors">
            <Mail size={16} />
          </a>
        </div>

        {/* Auth section */}
        {isAuthenticated && user ? (
          /* Usuario Autenticado */
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 p-1.5 rounded-full hover:bg-slate-50 border border-slate-100 transition-colors focus:outline-none"
            >
              {/* Avatar circular con color de la marca */}
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#1a4d2e] to-[#ea580c]/80 flex items-center justify-center text-white text-xs font-black shadow-inner">
                {getInitials(user.nombres)}
              </div>
              <span className="hidden md:inline text-xs font-black text-slate-700 max-w-[120px] truncate select-none">
                {user.nombres.split(' ')[0]}
              </span>
              <ChevronDown size={14} className="text-slate-400" />
            </button>

            {/* Dropdown Menu */}
            {dropdownOpen && (
              <div className="absolute right-0 mt-2.5 w-60 bg-white border border-slate-100 rounded-2xl shadow-xl py-2 z-50 transform origin-top-right transition-all animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="px-4 py-3 border-b border-slate-50">
                  <p className="text-xs font-black text-slate-800 truncate">{user.nombres}</p>
                  <p className="text-[10px] text-slate-400 font-medium truncate mt-0.5">{user.email}</p>
                </div>

                <div className="p-1">
                  <a
                    href="#perfil"
                    onClick={(e) => handlePortalRedirect(e, '/dashboard')}
                    className="flex items-center gap-2 px-3 py-2 text-xs font-semibold text-slate-600 hover:text-[#1a4d2e] hover:bg-slate-50 rounded-xl transition-colors"
                  >
                    <UserIcon size={16} className="text-slate-400" />
                    Mi Cuenta
                  </a>
                  <a
                    href="#planes"
                    onClick={(e) => handlePortalRedirect(e, '/dashboard/purchases')}
                    className="flex items-center gap-2 px-3 py-2 text-xs font-semibold text-slate-600 hover:text-[#1a4d2e] hover:bg-slate-50 rounded-xl transition-colors"
                  >
                    <UserCheck size={16} className="text-slate-400" />
                    Mis Suscripciones
                  </a>
                  <hr className="my-1 border-slate-100" />
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-3 py-2.5 text-xs font-bold text-red-600 hover:bg-red-50 rounded-xl transition-colors text-left"
                  >
                    <LogOut size={16} />
                    Cerrar Sesión
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Invitado (No autenticado) */
          <div className="flex items-center gap-2">
            <button
              onClick={() => openAuthModal('login')}
              className="py-2 px-4 rounded-xl text-xs font-black text-[#1a4d2e] border border-slate-200 hover:bg-slate-50 hover:border-slate-300 transition-all cursor-pointer"
            >
              Iniciar sesión
            </button>
            <button
              onClick={() => openAuthModal('register')}
              className="py-2.5 px-4.5 rounded-xl text-xs font-black text-white bg-[#1a4d2e] hover:bg-[#153e25] shadow-sm hover:shadow-md transition-all active:scale-[0.98] cursor-pointer"
            >
              Registrarse
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

