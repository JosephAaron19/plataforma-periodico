import React, { useState } from 'react';
import { Outlet, Link } from 'react-router-dom';
import { Newspaper, ChevronDown, Menu, X, Download, LogOut, LayoutDashboard } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const PublicLayout: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const { user, isAuthenticated, logout } = useAuth();

  const toggleDropdown = (name: string) => {
    if (activeDropdown === name) {
      setActiveDropdown(null);
    } else {
      setActiveDropdown(name);
    }
  };

  return (
    <div className="min-h-screen flex flex-col font-sans bg-[#030712] text-gray-300 selection:bg-brand-500/30 overflow-x-hidden">
      
      {/* Premium Navbar Header */}
      <header className="sticky top-0 z-50 bg-[#030712]/95 backdrop-blur-md border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="relative w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center shadow-lg shadow-brand-500/20 overflow-hidden">
              <div className="absolute inset-1 border-2 border-dark-900 rounded-md"></div>
              <Newspaper className="w-4 h-4 text-dark-900 z-10" />
            </div>
            <span className="text-xl font-extrabold text-white tracking-tight">
              DigitalSaaS
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            <div className="relative">
              <button 
                onClick={() => toggleDropdown('periodicos')}
                className="text-gray-300 hover:text-white font-medium text-sm flex items-center gap-1 transition-colors py-2"
              >
                Periódicos <ChevronDown className="w-3.5 h-3.5" />
              </button>
              {activeDropdown === 'periodicos' && (
                <div className="absolute top-full left-0 mt-1 w-48 bg-[#0b1220] border border-white/5 rounded-xl p-2 shadow-xl z-50">
                  <Link to="/catalog" className="block px-4 py-2 text-sm text-gray-300 hover:bg-white/5 hover:text-white rounded-lg">Nacionales</Link>
                  <Link to="/catalog" className="block px-4 py-2 text-sm text-gray-300 hover:bg-white/5 hover:text-white rounded-lg">Locales</Link>
                </div>
              )}
            </div>

            <a href="/#precios" className="text-gray-300 hover:text-white font-medium text-sm transition-colors py-2">
              Precios
            </a>
            
            <a href="/#como-funciona" className="text-gray-300 hover:text-white font-medium text-sm transition-colors py-2">
              Cómo funciona
            </a>

            <a href="#soporte" className="text-gray-300 hover:text-white font-medium text-sm transition-colors py-2">
              Soporte
            </a>

            <div className="relative">
              <button 
                onClick={() => toggleDropdown('empresa')}
                className="text-gray-300 hover:text-white font-medium text-sm flex items-center gap-1 transition-colors py-2"
              >
                Empresa <ChevronDown className="w-3.5 h-3.5" />
              </button>
              {activeDropdown === 'empresa' && (
                <div className="absolute top-full left-0 mt-1 w-48 bg-[#0b1220] border border-white/5 rounded-xl p-2 shadow-xl z-50">
                  <Link to="/about" className="block px-4 py-2 text-sm text-gray-300 hover:bg-white/5 hover:text-white rounded-lg">Nosotros</Link>
                  <Link to="/careers" className="block px-4 py-2 text-sm text-gray-300 hover:bg-white/5 hover:text-white rounded-lg">Contacto</Link>
                </div>
              )}
            </div>
          </nav>

          {/* Desktop Right CTAs */}
          <div className="hidden md:flex items-center gap-6">
            {isAuthenticated ? (
              <div className="relative">
                <button
                  onClick={() => toggleDropdown('user-menu')}
                  className="flex items-center gap-3 bg-white/5 hover:bg-white/10 px-4 py-2 rounded-xl border border-white/5 transition-all text-left"
                >
                  <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-brand-400 to-brand-600 text-white flex items-center justify-center font-bold shadow-sm">
                    {(user?.nombre || user?.email || 'U').charAt(0).toUpperCase()}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs font-semibold text-white leading-tight">
                      {user?.nombre || user?.email?.split('@')[0]}
                    </span>
                    <span className="text-[10px] text-gray-400 font-medium">
                      Conectado
                    </span>
                  </div>
                  <ChevronDown className="h-4 w-4 text-gray-400 ml-1" />
                </button>

                {activeDropdown === 'user-menu' && (
                  <div className="absolute top-full right-0 mt-2 w-56 bg-[#0b1220] border border-white/5 rounded-xl p-2 shadow-xl z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                    <div className="px-3 py-2 border-b border-white/5 mb-1.5">
                      <p className="text-xs text-gray-400 font-medium">Sesión activa</p>
                      <p className="text-sm text-white font-bold truncate">{user?.nombre || user?.email}</p>
                      <p className="text-xs text-gray-400 truncate">{user?.email}</p>
                    </div>

                    <Link
                      to="/dashboard"
                      className="flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-white/5 hover:text-white rounded-lg transition-colors"
                      onClick={() => setActiveDropdown(null)}
                    >
                      <LayoutDashboard className="w-4 h-4 text-brand-500" />
                      Ir al Dashboard
                    </Link>

                    <button
                      onClick={() => {
                        logout();
                        setActiveDropdown(null);
                      }}
                      className="flex items-center gap-2 w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors mt-1.5 border-t border-white/5 pt-2"
                    >
                      <LogOut className="w-4 h-4" />
                      Cerrar sesión
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <>
                <Link to="/login" className="text-gray-300 hover:text-white font-medium text-sm transition-colors">
                  Iniciar sesión
                </Link>
                <Link to="/register" className="px-4 py-2 bg-brand-500 hover:bg-brand-400 text-dark-900 font-bold text-sm rounded-lg transition-all shadow-lg shadow-brand-500/10">
                  Crear cuenta
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-gray-400 hover:text-white transition-colors"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Navigation Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-dark-900 border-b border-white/5 px-6 py-6 flex flex-col gap-4 animate-in fade-in slide-in-from-top-5 duration-200">
            <button 
              onClick={() => toggleDropdown('periodicos-mob')}
              className="text-gray-300 hover:text-white font-medium text-base flex items-center justify-between text-left py-2"
            >
              <span>Periódicos</span>
              <ChevronDown className={`w-4 h-4 transform transition-transform ${activeDropdown === 'periodicos-mob' ? 'rotate-180' : ''}`} />
            </button>
            {activeDropdown === 'periodicos-mob' && (
              <div className="pl-4 flex flex-col gap-2 border-l border-white/5">
                <Link to="/catalog" className="text-gray-400 py-1.5 text-sm">Nacionales</Link>
                <Link to="/catalog" className="text-gray-400 py-1.5 text-sm">Locales</Link>
              </div>
            )}

            <a href="/#precios" onClick={() => setMobileMenuOpen(false)} className="text-gray-300 hover:text-white font-medium text-base py-2">
              Precios
            </a>
            <a href="/#como-funciona" onClick={() => setMobileMenuOpen(false)} className="text-gray-300 hover:text-white font-medium text-base py-2">
              Cómo funciona
            </a>
            <a href="#soporte" onClick={() => setMobileMenuOpen(false)} className="text-gray-300 hover:text-white font-medium text-base py-2">
              Soporte
            </a>

            <button 
              onClick={() => toggleDropdown('empresa-mob')}
              className="text-gray-300 hover:text-white font-medium text-base flex items-center justify-between text-left py-2"
            >
              <span>Empresa</span>
              <ChevronDown className={`w-4 h-4 transform transition-transform ${activeDropdown === 'empresa-mob' ? 'rotate-180' : ''}`} />
            </button>
            {activeDropdown === 'empresa-mob' && (
              <div className="pl-4 flex flex-col gap-2 border-l border-white/5">
                <Link to="/about" className="text-gray-400 py-1.5 text-sm">Nosotros</Link>
                <Link to="/careers" className="text-gray-400 py-1.5 text-sm">Contacto</Link>
              </div>
            )}

            {isAuthenticated ? (
              <div className="flex flex-col gap-2 pt-2 border-t border-white/5">
                <div className="flex items-center gap-3 px-2 py-1">
                  <div className="h-10 w-10 rounded-full bg-gradient-to-tr from-brand-400 to-brand-600 text-white flex items-center justify-center font-bold shadow-sm">
                    {(user?.nombre || user?.email || 'U').charAt(0).toUpperCase()}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-sm font-semibold text-white">
                      {user?.nombre || user?.email?.split('@')[0]}
                    </span>
                    <span className="text-xs text-gray-400">
                      {user?.email}
                    </span>
                  </div>
                </div>
                <Link 
                  to="/dashboard" 
                  onClick={() => setMobileMenuOpen(false)} 
                  className="flex items-center justify-center gap-2 py-3 bg-brand-500 text-dark-900 font-bold rounded-lg hover:bg-brand-400 transition-all mt-2"
                >
                  <LayoutDashboard className="w-4 h-4" />
                  Ir al Dashboard
                </Link>
                <button 
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                  }} 
                  className="flex items-center justify-center gap-2 py-3 bg-red-500/10 text-red-400 font-medium rounded-lg hover:bg-red-500/20 transition-all"
                >
                  <LogOut className="w-4 h-4" />
                  Cerrar sesión
                </button>
              </div>
            ) : (
              <>
                <hr className="border-white/5 my-2" />
                <Link to="/login" onClick={() => setMobileMenuOpen(false)} className="text-center py-2 text-gray-300 hover:text-white font-medium">
                  Iniciar sesión
                </Link>
                <Link to="/register" onClick={() => setMobileMenuOpen(false)} className="text-center py-3 bg-brand-500 text-dark-900 font-bold rounded-lg hover:bg-brand-400 transition-all">
                  Crear cuenta
                </Link>
              </>
            )}
          </div>
        )}
      </header>

      {/* Main content slot */}
      <main className="flex-grow">
        <Outlet />
      </main>

      {/* Premium Footer */}
      <footer id="soporte" className="bg-[#02050a] text-gray-400 py-16 border-t border-white/5 relative z-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-8 mb-12">
            
            {/* Brand column */}
            <div className="lg:col-span-4 flex flex-col gap-4">
              <Link to="/" className="flex items-center gap-2">
                <div className="w-7 h-7 bg-brand-500 rounded-lg flex items-center justify-center overflow-hidden">
                  <Newspaper className="w-3.5 h-3.5 text-dark-900" />
                </div>
                <span className="text-lg font-bold text-white tracking-tight">DigitalSaaS</span>
              </Link>
              <p className="text-xs text-gray-500 leading-relaxed max-w-sm">
                Tu plataforma de confianza para leer los mejores periódicos digitales, cuando quieras y donde quieras.
              </p>
              
              {/* Social Icons (SVGs) */}
              <div className="flex gap-4 mt-2">
                <a href="#" aria-label="Facebook" className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center hover:bg-brand-500 hover:text-dark-900 transition-all text-gray-400">
                  <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                    <path d="M9 8H7v3h2v9h3v-9h3.6l.4-3H12V6c0-.9.6-1 1-1h3V2h-3c-3 0-5 1.8-5 5v1z"/>
                  </svg>
                </a>
                <a href="#" aria-label="Twitter" className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center hover:bg-brand-500 hover:text-dark-900 transition-all text-gray-400">
                  <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                    <path d="M18.2 2.4h3.3L14.3 11l8.5 11.3h-6.7L10.8 15.4l-6 6.9H1.6L9 13.9 1 3.2h6.9l4.8 6.4 5.5-7.2zm-1.2 17.5h1.8L7.1 5.1H5.1l11.9 14.8z"/>
                  </svg>
                </a>
                <a href="#" aria-label="Instagram" className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center hover:bg-brand-500 hover:text-dark-900 transition-all text-gray-400">
                  <svg className="w-4 h-4 stroke-current fill-none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
                    <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
                  </svg>
                </a>
                <a href="#" aria-label="LinkedIn" className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center hover:bg-brand-500 hover:text-dark-900 transition-all text-gray-400">
                  <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                  </svg>
                </a>
                <a href="#" aria-label="YouTube" className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center hover:bg-brand-500 hover:text-dark-900 transition-all text-gray-400">
                  <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                    <path d="M23.5 6.2c-.3-1.1-1.1-2-2.2-2.3-2-.5-10-.5-10-.5s-8 0-10 .5c-1.1.3-1.9 1.2-2.2 2.3-.5 2-.5 6.1-.5 6.1s0 4.1.5 6.1c.3 1.1 1.1 2 2.2 2.3 2 .5 10 .5 10 .5s8 0 10-.5c1.1-.3 1.9-1.2 2.2-2.3.5-2 .5-6.1.5-6.1s0-4.1-.5-6.1zM9.5 15.5V8.5l6.5 3.5-6.5 3.5z"/>
                  </svg>
                </a>
              </div>
            </div>

            {/* Nav Group 1: Explorar */}
            <div className="lg:col-span-2">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-4">Explorar</h4>
              <ul className="flex flex-col gap-2 text-xs">
                <li><Link to="/catalog" className="hover:text-white transition-colors">Periódicos</Link></li>
                <li><Link to="/catalog" className="hover:text-white transition-colors">Ediciones recientes</Link></li>
                <li><Link to="/catalog" className="hover:text-white transition-colors">Más populares</Link></li>
                <li><Link to="/catalog" className="hover:text-white transition-colors">Categorías</Link></li>
              </ul>
            </div>

            {/* Nav Group 2: Mi cuenta */}
            <div className="lg:col-span-2">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-4">Mi cuenta</h4>
              <ul className="flex flex-col gap-2 text-xs">
                <li><Link to="/login" className="hover:text-white transition-colors">Mis compras</Link></li>
                <li><Link to="/login" className="hover:text-white transition-colors">Favoritos</Link></li>
                <li><Link to="/login" className="hover:text-white transition-colors">Historial</Link></li>
                <li><Link to="/login" className="hover:text-white transition-colors">Perfil</Link></li>
              </ul>
            </div>

            {/* Nav Group 3: Ayuda */}
            <div className="lg:col-span-2">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-4">Ayuda</h4>
              <ul className="flex flex-col gap-2 text-xs">
                <li><Link to="/support" className="hover:text-white transition-colors">Centro de ayuda</Link></li>
                <li><Link to="/support" className="hover:text-white transition-colors">Preguntas frecuentes</Link></li>
                <li><Link to="/terms" className="hover:text-white transition-colors">Términos y condiciones</Link></li>
                <li><Link to="/support" className="hover:text-white transition-colors">Contacto</Link></li>
              </ul>
            </div>

            {/* App download column */}
            <div className="lg:col-span-2 flex flex-col gap-3">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Descarga nuestra app</h4>
              <a href="#" className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-colors text-white text-left animate-pulse">
                <Download className="w-4 h-4 text-brand-400 flex-shrink-0" />
                <div>
                  <div className="text-[7px] text-gray-500 uppercase leading-none font-bold">Consíguelo en el</div>
                  <div className="text-[10px] font-bold leading-tight">App Store</div>
                </div>
              </a>
              <a href="#" className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-colors text-white text-left animate-pulse">
                <Download className="w-4 h-4 text-brand-400 flex-shrink-0" />
                <div>
                  <div className="text-[7px] text-gray-500 uppercase leading-none font-bold">Disponible en</div>
                  <div className="text-[10px] font-bold leading-tight">Google Play</div>
                </div>
              </a>
            </div>

          </div>

          <hr className="border-white/5 my-8" />

          {/* Copyright */}
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-[11px] text-gray-600 font-medium">
            <span>© 2026 DigitalSaaS. Todos los derechos reservados.</span>
            <div className="flex gap-4">
              <a href="#" className="hover:text-gray-400 transition-colors">Privacidad</a>
              <a href="#" className="hover:text-gray-400 transition-colors">Términos de servicio</a>
            </div>
          </div>
        </div>
      </footer>

    </div>
  );
};

export default PublicLayout;
