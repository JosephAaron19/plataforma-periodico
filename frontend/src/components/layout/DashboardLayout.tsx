import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  BookCopy, 
  Eye, 
  CreditCard, 
  Users, 
  Settings, 
  Building2,
  LogOut,
  ChevronDown,
  Newspaper,
  Bookmark,
  Bell,
  Search,
  Heart,
  Calendar,
  Cloud,
  Download,
  User,
  ArrowRight,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const DashboardLayout: React.FC = () => {
  const { user, companies, activeCompanyId, setActiveCompany, logout } = useAuth();
  const location = useLocation();
  
  // Reader Tabs State
  const [activeReaderTab, setActiveReaderTab] = useState<'inicio' | 'mis-ediciones' | 'colecciones' | 'favoritos' | 'perfil'>('inicio');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<'todas' | 'dia' | 'mes'>('todas');

  const isPublisher = companies && companies.length > 0;
  const activeCompany = isPublisher ? (companies.find(c => c.id === activeCompanyId) || companies[0]) : null;

  // ----------------------------------------------------
  // READER DASHBOARD LAYOUT (when companies is empty)
  // ----------------------------------------------------
  if (!isPublisher) {
    // Mock user display name matching 'Carlos Sánchez' in mockup
    const userDisplayName = user?.nombre || 'Carlos Sánchez';
    const userInitials = userDisplayName
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .substring(0, 2) || 'CS';

    // Mock data for "Mis ediciones"
    const misEdiciones = [
      { id: '125', name: 'La Voz del Sur', date: '15 Mayo 2024', badge: 'Edición del día', badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200', cardColor: 'bg-[#ffc107]', logo: 'LA VOZ DEL SUR', textColor: 'text-slate-900' },
      { id: '842', name: 'El Pueblo', date: 'Mayo 2024', badge: 'Plan mensual', badgeColor: 'bg-blue-50 text-blue-700 border-blue-200', cardColor: 'bg-[#003882]', logo: 'El Pueblo', textColor: 'text-white' },
      { id: '310', name: 'Correo Arequipa', date: '14 Mayo 2024', badge: 'Edición del día', badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200', cardColor: 'bg-[#d90429]', logo: 'Correo', textColor: 'text-white' },
      { id: '038', name: 'Diario Opinión', date: 'Abril 2024', badge: 'Plan mensual', badgeColor: 'bg-blue-50 text-blue-700 border-blue-200', cardColor: 'bg-[#0d1e38]', logo: 'Diario Opinión', textColor: 'text-white' },
      { id: '210', name: 'Gestión', date: '13 Mayo 2024', badge: 'Edición del día', badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200', cardColor: 'bg-[#830a1c]', logo: 'GESTIÓN', textColor: 'text-white' }
    ];

    // Mock data for "Te puede interesar"
    const tePuedeInteresar = [
      { name: 'El Comercio', logoText: 'El Comercio', bg: 'bg-[#ffc107] text-black', desc: 'Información nacional e internacional' },
      { name: 'Perú 21', logoText: 'Perú 21', bg: 'bg-[#0f3d7a] text-white', desc: 'Actualidad y análisis en profundidad' },
      { name: 'RPP', logoText: 'RPP', bg: 'bg-[#fec006] text-black', desc: 'Noticias al instante, las 24 horas' },
      { name: 'Exitosa', logoText: 'EXITOSA', bg: 'bg-[#d90429] text-white', desc: 'La voz de los que no tienen voz' },
      { name: 'La República', logoText: 'La República', bg: 'bg-[#c1121f] text-white', desc: 'Periodismo con independencia' }
    ];

    // Mock activity list
    const actividades = [
      { type: 'read', text: 'Leiste una edición', detail: 'La Voz del Sur', sub: 'Edición del 15 Mayo 2024', time: 'Hoy, 09:15 AM', icon: BookCopy, iconColor: 'text-emerald-600 bg-emerald-50' },
      { type: 'download', text: 'Descargaste una edición', detail: 'El Pueblo', sub: 'Edición de Mayo 2024', time: 'Ayer, 04:30 PM', icon: Download, iconColor: 'text-emerald-600 bg-emerald-50' },
      { type: 'favorite', text: 'Marcaste como favorito', detail: 'Correo Arequipa', sub: 'Edición del 14 Mayo 2024', time: 'Ayer, 11:20 AM', icon: Heart, iconColor: 'text-amber-500 bg-amber-50' },
      { type: 'read', text: 'Abriste una edición', detail: 'Diario Opinión', sub: 'Edición de Abril 2024', time: '12 Mayo, 08:10 AM', icon: BookCopy, iconColor: 'text-emerald-600 bg-emerald-50' },
      { type: 'bookmark', text: 'Guardaste una edición', detail: 'Gestión', sub: 'Edición del 13 Mayo 2024', time: '11 Mayo, 06:45 PM', icon: Bookmark, iconColor: 'text-emerald-600 bg-emerald-50' },
      { type: 'session', text: 'Iniciaste sesión', detail: 'Dispositivo: Chrome', sub: 'Arequipa, Perú', time: '10 Mayo, 08:10 AM', icon: User, iconColor: 'text-emerald-600 bg-emerald-50' }
    ];

    return (
      <div className="flex h-screen bg-slate-50 overflow-hidden font-sans text-slate-800">
        
        {/* Reader Sidebar */}
        <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between flex-shrink-0 z-20">
          <div>
            {/* Header / Logo */}
            <div className="h-16 flex items-center px-6 border-b border-slate-100">
              <Link to="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center shadow-md">
                  <Newspaper className="w-4 h-4 text-white" />
                </div>
                <span className="text-lg font-black text-slate-900 tracking-tight">DigitalSaaS</span>
              </Link>
            </div>

            {/* Navigation Options */}
            <div className="px-4 py-6 space-y-7">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-3 block mb-3">
                  Navegación
                </span>
                <nav className="space-y-1">
                  <button
                    onClick={() => setActiveReaderTab('inicio')}
                    className={`flex items-center w-full px-3 py-2.5 text-xs font-bold rounded-xl transition-all duration-150 ${
                      activeReaderTab === 'inicio'
                        ? 'bg-brand-50 text-brand-700 shadow-sm'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    }`}
                  >
                    <LayoutDashboard className={`mr-2.5 h-4.5 w-4.5 ${activeReaderTab === 'inicio' ? 'text-brand-600' : 'text-slate-400'}`} />
                    Inicio
                  </button>

                  <button
                    onClick={() => setActiveReaderTab('mis-ediciones')}
                    className={`flex items-center w-full px-3 py-2.5 text-xs font-bold rounded-xl transition-all duration-150 ${
                      activeReaderTab === 'mis-ediciones'
                        ? 'bg-brand-50 text-brand-700 shadow-sm'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    }`}
                  >
                    <BookCopy className={`mr-2.5 h-4.5 w-4.5 ${activeReaderTab === 'mis-ediciones' ? 'text-brand-600' : 'text-slate-400'}`} />
                    Mis ediciones
                  </button>

                  <button
                    onClick={() => setActiveReaderTab('colecciones')}
                    className={`flex items-center w-full px-3 py-2.5 text-xs font-bold rounded-xl transition-all duration-150 ${
                      activeReaderTab === 'colecciones'
                        ? 'bg-brand-50 text-brand-700 shadow-sm'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    }`}
                  >
                    <Newspaper className={`mr-2.5 h-4.5 w-4.5 ${activeReaderTab === 'colecciones' ? 'text-brand-600' : 'text-slate-400'}`} />
                    Colecciones
                  </button>

                  <button
                    onClick={() => setActiveReaderTab('favoritos')}
                    className={`flex items-center w-full px-3 py-2.5 text-xs font-bold rounded-xl transition-all duration-150 ${
                      activeReaderTab === 'favoritos'
                        ? 'bg-brand-50 text-brand-700 shadow-sm'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    }`}
                  >
                    <Heart className={`mr-2.5 h-4.5 w-4.5 ${activeReaderTab === 'favoritos' ? 'text-brand-600' : 'text-slate-400'}`} />
                    Favoritos
                  </button>
                </nav>
              </div>

              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-3 block mb-3">
                  Cuenta
                </span>
                <nav className="space-y-1">
                  <button
                    onClick={() => setActiveReaderTab('perfil')}
                    className={`flex items-center w-full px-3 py-2.5 text-xs font-bold rounded-xl transition-all duration-150 ${
                      activeReaderTab === 'perfil'
                        ? 'bg-brand-50 text-brand-700 shadow-sm'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    }`}
                  >
                    <User className={`mr-2.5 h-4.5 w-4.5 ${activeReaderTab === 'perfil' ? 'text-brand-600' : 'text-slate-400'}`} />
                    Perfil
                  </button>

                  <button
                    onClick={logout}
                    className="flex items-center w-full px-3 py-2.5 text-xs font-bold rounded-xl text-red-600 hover:bg-red-50 hover:text-red-700 transition-all"
                  >
                    <LogOut className="mr-2.5 h-4.5 w-4.5 text-red-500" />
                    Cerrar sesión
                  </button>
                </nav>
              </div>
            </div>

          </div>

          {/* Promotion Banner Box inside Sidebar */}
          <div className="p-4 m-4 bg-slate-50 border border-slate-200 rounded-2xl shadow-sm text-left">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-white mb-3 shadow-md shadow-brand-500/10">
              <Newspaper className="w-4 h-4" />
            </div>
            <h4 className="text-xs font-black text-slate-900 mb-1.5 leading-snug">¿Necesitas más ediciones?</h4>
            <p className="text-[10px] text-slate-500 font-semibold leading-relaxed mb-3">
              Descubre todos los periódicos disponibles y elige el plan que mejor se adapte a ti.
            </p>
            <Link 
              to="/catalog" 
              className="inline-flex items-center gap-1 text-[10px] font-bold text-brand-700 hover:text-brand-800 transition-colors uppercase tracking-wider"
            >
              Explorar periódicos <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </aside>

        {/* Reader Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          
          {/* Header */}
          <header className="h-16 bg-white border-b border-slate-200/60 flex items-center justify-between px-8 shadow-sm flex-shrink-0 z-10">
            {/* Greeting */}
            <div className="text-left">
              <h1 className="text-lg font-black text-slate-900 leading-tight">
                ¡Hola, {userDisplayName}! 👋
              </h1>
              <p className="text-[10px] lg:text-[11px] text-slate-500 font-bold mt-0.5">
                Explora y disfruta todas las ediciones que has adquirido.
              </p>
            </div>

            {/* Search Input */}
            <div className="relative w-64 lg:w-80 hidden md:block">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-400">
                <Search className="w-4 h-4" />
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Buscar periódicos o ediciones..."
                className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-700 placeholder-slate-400 focus:outline-none focus:border-brand-500 focus:bg-white transition-all font-semibold"
              />
            </div>

            {/* Notifications & Profile dropdown */}
            <div className="flex items-center gap-4">
              
              {/* Notification Bell */}
              <button className="relative p-2 text-slate-500 hover:text-slate-800 transition-colors rounded-xl hover:bg-slate-50">
                <Bell className="w-5 h-5" />
                <span className="absolute top-1 right-1 w-4 h-4 bg-brand-500 text-white text-[8px] font-bold rounded-full flex items-center justify-center border border-white">
                  3
                </span>
              </button>

              <div className="h-8 w-px bg-slate-200"></div>

              {/* User Profiling */}
              <button className="flex items-center gap-2 hover:bg-slate-100 p-1.5 rounded-xl transition-all">
                <div className="h-8 w-8 rounded-full bg-brand-500 text-white flex items-center justify-center font-black text-xs shadow-sm">
                  {userInitials}
                </div>
                <div className="text-left hidden sm:block">
                  <p className="text-xs font-bold text-slate-900 leading-tight">{userDisplayName}</p>
                  <p className="text-[9px] text-slate-400 leading-none mt-0.5 font-bold">{user?.email}</p>
                </div>
                <ChevronDown className="h-3.5 w-3.5 text-slate-400 ml-1 hidden sm:block" />
              </button>
            </div>
          </header>

          {/* Body content wrapped in grid split with activity list */}
          <div className="flex-1 flex overflow-hidden">
            
            {/* Center Area (Tab contents, lists, highlights) */}
            <main className="flex-1 overflow-x-hidden overflow-y-auto bg-slate-50 p-8 space-y-8">
              {activeReaderTab === 'inicio' && (
                <>
                  {/* Explorar mis ediciones Tabs row */}
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200/50 pb-5 text-left">
                    <div>
                      <h2 className="text-xs font-black text-slate-900 uppercase tracking-widest">
                        Explorar mis ediciones
                      </h2>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
                      <div className="flex bg-slate-200/60 p-0.5 rounded-xl border border-slate-200">
                        <button 
                          onClick={() => setActiveFilter('todas')}
                          className={`px-3 py-1.5 text-[10px] font-bold rounded-lg transition-all ${activeFilter === 'todas' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'}`}
                        >
                          Todas
                        </button>
                        <button 
                          onClick={() => setActiveFilter('dia')}
                          className={`px-3 py-1.5 text-[10px] font-bold rounded-lg transition-all ${activeFilter === 'dia' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'}`}
                        >
                          Por día
                        </button>
                        <button 
                          onClick={() => setActiveFilter('mes')}
                          className={`px-3 py-1.5 text-[10px] font-bold rounded-lg transition-all ${activeFilter === 'mes' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'}`}
                        >
                          Plan mensual
                        </button>
                      </div>

                      {/* Dropdown Filters */}
                      <button className="bg-white border border-slate-200 px-3 py-1.5 rounded-xl text-[10px] font-bold text-slate-600 hover:bg-slate-50 transition-all flex items-center gap-1.5 shadow-sm">
                        <Calendar className="w-3.5 h-3.5 text-slate-500" /> Fecha <ChevronDown className="w-3 h-3" />
                      </button>
                      <button className="bg-white border border-slate-200 px-3 py-1.5 rounded-xl text-[10px] font-bold text-slate-600 hover:bg-slate-50 transition-all flex items-center gap-1.5 shadow-sm">
                        Más recientes <ChevronDown className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  {/* Mis ediciones list section */}
                  <div className="space-y-4 text-left">
                    <div className="flex justify-between items-end">
                      <div>
                        <h3 className="text-base font-black text-slate-900">Mis ediciones</h3>
                        <p className="text-[10px] text-slate-500 font-semibold mt-0.5">Periódicos que has comprado o a los que estás suscrito.</p>
                      </div>
                      <Link to="/catalog" className="text-xs font-bold text-brand-700 hover:text-brand-800 flex items-center gap-0.5 transition-colors">
                        Ver todas <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>

                    {/* Cards grid */}
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-5">
                      {misEdiciones
                        .filter(ed => {
                          if (activeFilter === 'dia') return ed.badge === 'Edición del día';
                          if (activeFilter === 'mes') return ed.badge === 'Plan mensual';
                          return true;
                        })
                        .map((ed, i) => (
                          <div key={i} className="group flex flex-col bg-white border border-slate-200 rounded-2xl overflow-hidden hover:shadow-md transition-all duration-300">
                            {/* Card Cover */}
                            <div className="aspect-[3/4] bg-slate-50 p-3.5 border-b border-slate-200 relative flex items-center justify-center">
                              <div className="w-full h-full bg-white shadow-sm rounded-lg flex flex-col p-2 transform group-hover:scale-[1.01] transition-transform duration-300 overflow-hidden relative">
                                {/* Cover Banner logo */}
                                <div className={`w-full py-1 text-center text-[7px] font-serif font-black tracking-tight mb-2 ${ed.cardColor} ${ed.textColor || 'text-white'} rounded-md`}>
                                  {ed.logo}
                                </div>
                                <div className="flex-1 flex flex-col gap-1 overflow-hidden">
                                  <div className="h-0.5 bg-slate-900 w-full mb-0.5"></div>
                                  <div className="h-1 bg-slate-200 w-full mb-0.5"></div>
                                  <div className="h-1 bg-slate-300 w-3/4"></div>
                                  <div className="h-10 bg-slate-50 rounded border border-slate-200 mt-1 flex items-center justify-center">
                                    <Newspaper className="w-3.5 h-3.5 text-slate-300" />
                                  </div>
                                </div>
                                {/* Badge */}
                                <div className={`mt-2 text-[5.5px] font-extrabold border rounded px-1 py-0.5 w-fit uppercase ${ed.badgeColor}`}>
                                  {ed.badge}
                                </div>
                              </div>
                            </div>
                            
                            {/* Details */}
                            <div className="p-3.5 flex flex-col flex-1 w-full text-left">
                              <h4 className="font-black text-slate-800 text-xs truncate group-hover:text-brand-700 transition-all">{ed.name}</h4>
                              <p className="text-[10px] text-slate-500 font-bold mt-0.5">{ed.date}</p>
                              
                              <div className="mt-3.5 flex items-center gap-2">
                                <Link 
                                  to={`/editions/${ed.id}`} 
                                  className="flex-1 py-1.5 text-[10px] font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-lg group-hover:bg-brand-500 group-hover:text-dark-900 group-hover:border-brand-400 transition-all text-center"
                                >
                                  Leer ahora
                                </Link>
                                <button className="p-1.5 rounded-lg border border-slate-200 text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors">
                                  <Bookmark className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            </div>
                          </div>
                      ))}
                    </div>
                  </div>

                  {/* Highlights Banner row */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-left pt-2">
                    
                    {/* Item 1 */}
                    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
                      <div className="w-10 h-10 rounded-full bg-brand-500/10 flex items-center justify-center text-brand-700 flex-shrink-0">
                        <Calendar className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="text-xs font-black text-slate-900 leading-snug">Accede cuando quieras</h4>
                        <p className="text-[10px] text-slate-500 leading-relaxed font-bold mt-0.5">
                          Lee tus ediciones en cualquier momento y desde cualquier dispositivo.
                        </p>
                      </div>
                    </div>

                    {/* Item 2 */}
                    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
                      <div className="w-10 h-10 rounded-full bg-brand-500/10 flex items-center justify-center text-brand-700 flex-shrink-0">
                        <Cloud className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="text-xs font-black text-slate-900 leading-snug">Guarda y organiza</h4>
                        <p className="text-[10px] text-slate-500 leading-relaxed font-bold mt-0.5">
                          Tus ediciones se guardan automáticamente en tu biblioteca personal.
                        </p>
                      </div>
                    </div>

                    {/* Item 3 */}
                    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm flex items-center gap-4 hover:shadow-md transition-shadow">
                      <div className="w-10 h-10 rounded-full bg-brand-500/10 flex items-center justify-center text-brand-700 flex-shrink-0">
                        <Heart className="w-5 h-5 animate-pulse" />
                      </div>
                      <div>
                        <h4 className="text-xs font-black text-slate-900 leading-snug">Tus favoritos</h4>
                        <p className="text-[10px] text-slate-500 leading-relaxed font-bold mt-0.5">
                          Marca y encuentra fácilmente tus periódicos y ediciones favoritas.
                        </p>
                      </div>
                    </div>

                  </div>

                  {/* Te puede interesar colored brand list */}
                  <div className="space-y-4 text-left">
                    <div className="flex justify-between items-end">
                      <div>
                        <h3 className="text-base font-black text-slate-900">Te puede interesar</h3>
                        <p className="text-[10px] text-slate-500 font-semibold mt-0.5">Descubre más periódicos que podrían interesarte.</p>
                      </div>
                      <Link to="/catalog" className="text-xs font-bold text-brand-700 hover:text-brand-800 flex items-center gap-0.5 transition-colors">
                        Ver todos los periódicos <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>

                    {/* Colored Cards grid */}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-5">
                      {tePuedeInteresar.map((item, i) => (
                        <div key={i} className="bg-white border border-slate-200 rounded-2xl p-4 flex flex-col justify-between hover:shadow-md transition-all duration-300 min-h-[160px] text-center">
                          {/* Banner logo */}
                          <div className={`w-full py-3 text-xs font-serif font-black tracking-tight rounded-xl flex items-center justify-center ${item.bg}`}>
                            {item.logoText}
                          </div>
                          
                          <p className="text-[10px] text-slate-500 font-semibold my-3.5 leading-snug">
                            {item.desc}
                          </p>

                          <Link 
                            to="/catalog" 
                            className="w-full py-1.5 text-[9px] font-bold text-slate-600 bg-slate-50 border border-slate-200 rounded-lg hover:bg-brand-50 text-brand-700 hover:border-brand-300 transition-colors"
                          >
                            Ver ediciones
                          </Link>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {activeReaderTab === 'mis-ediciones' && (
                <div className="bg-white p-6 rounded-2xl border border-slate-200 text-left space-y-4">
                  <h2 className="text-lg font-black text-slate-900">Mis Ediciones Completas</h2>
                  <p className="text-xs text-slate-400 font-bold">Aquí encontrarás todas tus compras y suscripciones activas.</p>
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 pt-4">
                    {misEdiciones.map((ed, i) => (
                      <div key={i} className="bg-slate-50 p-4 border border-slate-200 rounded-xl flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-[8px] ${ed.textColor || 'text-white'} font-serif font-black ${ed.cardColor}`}>{ed.logo.substring(0,2)}</div>
                          <div>
                            <h4 className="text-xs font-bold text-slate-900">{ed.name}</h4>
                            <p className="text-[9px] text-slate-500 font-bold">{ed.date}</p>
                          </div>
                        </div>
                        <Link to={`/editions/${ed.id}`} className="text-[10px] font-bold text-brand-700 hover:underline">Leer</Link>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeReaderTab === 'colecciones' && (
                <div className="bg-white p-6 rounded-2xl border border-slate-200 text-left space-y-4">
                  <h2 className="text-lg font-black text-slate-900">Mis Colecciones</h2>
                  <p className="text-xs text-slate-400 font-semibold">Agrupa tus periódicos y clasifica tus artículos de prensa favoritos.</p>
                  <div className="text-center py-12 text-slate-400 text-xs font-semibold">
                    No tienes colecciones creadas todavía. Crea una colección en el visor de lectura.
                  </div>
                </div>
              )}

              {activeReaderTab === 'favoritos' && (
                <div className="bg-white p-6 rounded-2xl border border-slate-200 text-left space-y-4">
                  <h2 className="text-lg font-black text-slate-900">Ediciones Favoritas</h2>
                  <p className="text-xs text-slate-400 font-bold">Tus diarios marcados para lectura rápida.</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
                    {misEdiciones.slice(0, 2).map((ed, i) => (
                      <div key={i} className="bg-slate-50 p-4 border border-slate-200 rounded-xl flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded bg-brand-500 text-white flex items-center justify-center"><Heart className="w-4.5 h-4.5 fill-white text-white" /></div>
                          <div>
                            <h4 className="text-xs font-bold text-slate-900">{ed.name}</h4>
                            <p className="text-[9px] text-slate-500 font-bold">Marcado como preferido</p>
                          </div>
                        </div>
                        <Link to={`/editions/${ed.id}`} className="text-[10px] font-bold text-brand-700 hover:underline">Ir a leer</Link>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeReaderTab === 'perfil' && (
                <div className="bg-white p-6 rounded-2xl border border-slate-200 text-left space-y-6">
                  <h2 className="text-lg font-black text-slate-900">Detalles de Perfil</h2>
                  <div className="flex items-center gap-4 pb-4 border-b border-slate-100">
                    <div className="h-14 w-14 rounded-full bg-emerald-500 text-white flex items-center justify-center font-black text-lg shadow-sm">{userInitials}</div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">{userDisplayName}</h3>
                      <p className="text-xs text-slate-400 font-semibold">{user?.email}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs font-semibold text-slate-600">
                    <div className="space-y-1.5">
                      <span className="text-[10px] uppercase font-bold text-slate-500 block">Nombre Completo</span>
                      <p className="bg-slate-50 px-4 py-2 rounded-xl border border-slate-200 text-slate-800 font-semibold">{userDisplayName}</p>
                    </div>
                    <div className="space-y-1.5">
                      <span className="text-[10px] uppercase font-bold text-slate-500 block">Correo Electrónico</span>
                      <p className="bg-slate-50 px-4 py-2 rounded-xl border border-slate-200 text-slate-800 font-semibold">{user?.email}</p>
                    </div>
                  </div>
                </div>
              )}
            </main>

            {/* Reader Right Activity Sidebar */}
            <aside className="w-80 bg-white border-l border-slate-200 overflow-y-auto p-6 hidden lg:flex flex-col justify-between flex-shrink-0 text-left">
              <div>
                <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest mb-1.5">
                  Actividad reciente
                </h3>
                <p className="text-[10px] text-slate-400 font-semibold mb-6">
                  Tus últimas acciones en la plataforma.
                </p>

                {/* Activity List */}
                <div className="space-y-5">
                  {actividades.map((act, i) => {
                    const ActIcon = act.icon;
                    return (
                      <div key={i} className="flex items-start justify-between gap-3 text-left">
                        <div className="flex items-start gap-3">
                          {/* Icon wrapper */}
                          <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${act.iconColor}`}>
                            <ActIcon className="w-4.5 h-4.5" />
                          </div>
                          <div>
                            <p className="text-xs font-black text-slate-800 leading-tight">
                              {act.text}
                            </p>
                            <p className="text-[10px] text-slate-600 font-bold mt-0.5 leading-snug">
                              {act.detail}
                            </p>
                            {act.sub && (
                              <p className="text-[9px] text-slate-400 font-medium leading-none mt-0.5">
                                {act.sub}
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="text-[8px] text-slate-400 font-bold whitespace-nowrap mt-0.5 text-right flex-shrink-0">
                          {act.time}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* View all activity button */}
              <button className="w-full mt-6 py-2.5 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-xl hover:bg-slate-100 hover:text-slate-900 hover:border-slate-300 transition-all text-center">
                Ver toda la actividad
              </button>
            </aside>

          </div>
        </div>

      </div>
    );
  }

  // ----------------------------------------------------
  // PUBLISHER DASHBOARD LAYOUT (when user has companies)
  // ----------------------------------------------------

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Ediciones', href: '/dashboard/editions', icon: BookCopy },
    { name: 'Visor', href: '/dashboard/viewer', icon: Eye },
    { name: 'Compras', href: '/dashboard/purchases', icon: CreditCard },
    { name: 'Usuarios', href: '/dashboard/users', icon: Users },
    { name: 'Planes', href: '/dashboard/plans', icon: Building2 },
    { name: 'Configuración', href: '/dashboard/settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-dark-900 flex flex-col shadow-xl flex-shrink-0">
        <div className="h-16 flex items-center px-6 border-b border-dark-800">
          <BookCopy className="h-8 w-8 text-brand-500 mr-2" />
          <span className="text-white text-xl font-bold tracking-wide">DigitalSaaS</span>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-3 py-3 text-sm font-medium rounded-lg transition-colors duration-150 ${
                  isActive
                    ? 'bg-brand-600 text-white shadow-md'
                    : 'text-gray-300 hover:bg-dark-800 hover:text-white'
                }`}
              >
                <Icon className={`mr-3 h-5 w-5 flex-shrink-0 ${isActive ? 'text-white' : 'text-gray-400'}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-dark-800">
          <button
            onClick={logout}
            className="flex items-center w-full px-3 py-3 text-sm font-medium text-gray-300 rounded-lg hover:bg-dark-800 hover:text-white transition-colors"
          >
            <LogOut className="mr-3 h-5 w-5 text-gray-400" />
            Cerrar Sesión
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8 shadow-sm flex-shrink-0 z-10">
          
          {/* Company Selector */}
          <div className="flex items-center">
            <div className="relative group cursor-pointer">
              <div className="flex items-center space-x-2 bg-gray-50 hover:bg-gray-100 px-4 py-2 rounded-lg border border-gray-200 transition-colors">
                <div className="h-8 w-8 bg-brand-100 text-brand-700 rounded-md flex items-center justify-center font-bold">
                  {(activeCompany?.nombre_comercial || activeCompany?.nombre || 'E').charAt(0).toUpperCase()}
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-gray-900 leading-tight">
                    {activeCompany?.nombre_comercial || activeCompany?.nombre || 'Empresa'}
                  </span>
                  <span className="text-xs text-gray-500 font-medium">
                    {activeCompany?.role || 'Admin'}
                  </span>
                </div>
                <ChevronDown className="h-4 w-4 text-gray-400 ml-2" />
              </div>
              
              {/* Dropdown for Companies */}
              <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                <div className="p-2">
                  <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-3">
                    Tus Empresas
                  </div>
                  {companies.map((company) => (
                    <button
                      key={company.id}
                      onClick={() => setActiveCompany(company.id)}
                      className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors flex items-center ${
                        activeCompanyId === company.id 
                          ? 'bg-brand-50 text-brand-700 font-medium' 
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <div className="h-6 w-6 rounded bg-gray-100 text-gray-600 flex items-center justify-center mr-2 text-xs font-bold">
                        {(company.nombre_comercial || company.nombre || 'E').charAt(0).toUpperCase()}
                      </div>
                      <span className="truncate">{company.nombre_comercial || company.nombre}</span>
                    </button>
                  ))}
                  <div className="border-t border-gray-100 mt-2 pt-2">
                    <Link to="/onboarding/create-company" className="block w-full text-left px-3 py-2 text-sm text-brand-600 hover:bg-brand-50 rounded-md transition-colors font-medium">
                      + Crear nueva empresa
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* User Profile */}
          <div className="flex items-center space-x-4">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-medium text-gray-900">{user?.nombre || user?.email}</div>
              <div className="text-xs text-gray-500">{user?.email}</div>
            </div>
            <div className="h-10 w-10 rounded-full bg-gradient-to-tr from-brand-400 to-brand-600 text-white flex items-center justify-center font-bold shadow-sm">
              {(user?.nombre || user?.email || 'U').charAt(0).toUpperCase()}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
