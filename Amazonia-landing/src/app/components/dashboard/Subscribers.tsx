import React, { useState, useEffect } from 'react';
import { 
  Users as UsersIcon, Search, RefreshCw, Loader2, Calendar, 
  CreditCard, Check, Ban, BookOpen, AlertCircle
} from 'lucide-react';
import { useAuth } from '../../contexts/auth';
import api from '../../services/api';
import { toast } from 'sonner';

interface Subscriber {
  id: number;
  plan_code: 'diario' | 'mensual' | 'anual';
  plan_name: string;
  fecha_inicio: string;
  fecha_vencimiento: string;
  estado: 'ACTIVO' | 'VENCIDO';
  monto: string;
  moneda: string;
  usuario: {
    id: number;
    nombres: string;
    apellidos: string | null;
    correo: string;
  };
  pago_metodo: string;
  referencia: string;
}

const Subscribers: React.FC = () => {
  const { activeCompanyId } = useAuth();
  
  const [subscribers, setSubscribers] = useState<Subscriber[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'TODOS' | 'ACTIVO' | 'VENCIDO'>('TODOS');
  const [planFilter, setPlanFilter] = useState<'TODOS' | 'diario' | 'mensual' | 'anual'>('TODOS');

  const fetchSubscribers = async () => {
    if (!activeCompanyId) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    try {
      const res = await api.get('admin/subscribers/');
      setSubscribers(res.data || []);
    } catch (err) {
      console.error("Error al cargar suscriptores:", err);
      toast.error("Error al cargar la lista de suscriptores");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscribers();
  }, [activeCompanyId]);

  const getInitials = (nombres: string, apellidos: string | null) => {
    const fLetter = nombres ? nombres.charAt(0) : '';
    const sLetter = apellidos ? apellidos.charAt(0) : '';
    return (fLetter + sLetter).toUpperCase() || 'U';
  };

  const getPlanBadgeColor = (planCode: string) => {
    switch (planCode) {
      case 'anual':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'mensual':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  // Filter subscribers locally by search query, plan type, and status
  const filteredSubscribers = subscribers.filter(sub => {
    const fullName = `${sub.usuario.nombres} ${sub.usuario.apellidos || ''}`.toLowerCase();
    const email = sub.usuario.correo.toLowerCase();
    const reference = (sub.referencia || '').toLowerCase();
    const query = searchQuery.toLowerCase();
    
    const matchesSearch = fullName.includes(query) || email.includes(query) || reference.includes(query);
    const matchesStatus = statusFilter === 'TODOS' || sub.estado === statusFilter;
    const matchesPlan = planFilter === 'TODOS' || sub.plan_code === planFilter;
    
    return matchesSearch && matchesStatus && matchesPlan;
  });

  // Calculate metrics
  const totalCount = subscribers.length;
  const activeCount = subscribers.filter(s => s.estado === 'ACTIVO').length;
  const expiredCount = subscribers.filter(s => s.estado === 'VENCIDO').length;
  
  const annualCount = subscribers.filter(s => s.plan_code === 'anual' && s.estado === 'ACTIVO').length;
  const monthlyCount = subscribers.filter(s => s.plan_code === 'mensual' && s.estado === 'ACTIVO').length;
  const dailyCount = subscribers.filter(s => s.plan_code === 'diario' && s.estado === 'ACTIVO').length;

  return (
    <div className="max-w-[90rem] mx-auto space-y-8 animate-in fade-in duration-300 text-left">
      
      {/* Header section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200/60 pb-6">
        <div>
          <h1 className="text-2xl font-black text-slate-900 leading-tight">
            Control de suscriptores
          </h1>
          <p className="text-xs text-slate-500 font-semibold mt-1.5">
            Monitorea los accesos de usuarios activos en planes de lectura del periódico.
          </p>
        </div>
        <div>
          <button 
            onClick={fetchSubscribers}
            className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-bold text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 cursor-pointer shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Actualizar datos
          </button>
        </div>
      </div>

      {/* Stats Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { title: 'Total Suscriptores', value: totalCount, icon: UsersIcon, color: 'text-[#1a4d2e] bg-emerald-50' },
          { title: 'Suscripciones Activas', value: activeCount, icon: Check, color: 'text-emerald-600 bg-emerald-50' },
          { title: 'Suscripciones Vencidas', value: expiredCount, icon: Ban, color: 'text-rose-600 bg-rose-50' },
          { title: 'Suscritos Anuales Activos', value: annualCount, icon: BookOpen, color: 'text-blue-600 bg-blue-50' }
        ].map((card, i) => {
          const Icon = card.icon;
          return (
            <div key={i} className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{card.title}</span>
                <h3 className="text-2xl font-black text-slate-800 mt-1">{card.value}</h3>
              </div>
              <div className={`p-3 rounded-xl ${card.color}`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid: filter and table */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Side: Table & Filters (col-span-3) */}
        <div className="lg:col-span-3 bg-white border border-slate-200 rounded-3xl shadow-sm overflow-hidden flex flex-col justify-between">
          
          <div>
            {/* Table Filter Actions Bar */}
            <div className="p-5 border-b border-slate-200/80 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-50/50">
              
              {/* Tabs Filter */}
              <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200/60">
                {[
                  { label: 'Todos', value: 'TODOS' },
                  { label: 'Activos', value: 'ACTIVO' },
                  { label: 'Vencidos', value: 'VENCIDO' }
                ].map((tab) => (
                  <button
                    key={tab.value}
                    onClick={() => setStatusFilter(tab.value as any)}
                    className={`px-4 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer ${
                      statusFilter === tab.value 
                        ? 'bg-white text-slate-900 shadow-sm' 
                        : 'text-slate-500 hover:text-slate-900'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Search bar */}
              <div className="flex items-center gap-3 w-full md:w-auto">
                <div className="relative flex-grow md:flex-grow-0 md:w-72">
                  <Search className="absolute left-3.5 top-2.5 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Buscar por usuario o referencia..."
                    className="w-full bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-700 placeholder-slate-400 focus:outline-none focus:border-[#1a4d2e] transition-all font-semibold"
                  />
                </div>
              </div>
            </div>

            {/* Table Area */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50/75 border-b border-slate-200 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    <th className="px-6 py-4">Usuario</th>
                    <th className="px-6 py-4">Plan contratado</th>
                    <th className="px-6 py-4">Fecha inicio</th>
                    <th className="px-6 py-4">Fecha vencimiento</th>
                    <th className="px-6 py-4">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 text-xs font-semibold text-slate-700">
                  {isLoading ? (
                    <tr>
                      <td colSpan={5} className="py-24 text-center">
                        <div className="flex flex-col items-center justify-center gap-3">
                          <Loader2 className="w-8 h-8 text-[#1a4d2e] animate-spin" />
                          <span className="text-slate-400 font-bold text-sm">Cargando suscriptores...</span>
                        </div>
                      </td>
                    </tr>
                  ) : filteredSubscribers.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-24 text-center">
                        <div className="flex flex-col items-center justify-center gap-2 max-w-sm mx-auto text-slate-400">
                          <UsersIcon className="w-12 h-12 text-slate-300" />
                          <h4 className="font-bold text-slate-700 text-sm mt-2">No se encontraron suscriptores</h4>
                          <p className="text-[11px] leading-relaxed text-center">No hay registros de suscriptores con los filtros seleccionados.</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    filteredSubscribers.map((sub) => {
                      const initials = getInitials(sub.usuario.nombres, sub.usuario.apellidos);
                      return (
                        <tr key={sub.id} className="hover:bg-slate-50/40 transition-colors">
                          
                          {/* Avatar y Datos Personales */}
                          <td className="px-6 py-4.5">
                            <div className="flex items-center gap-3.5">
                              <div className="w-10 h-10 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center text-[#1a4d2e] font-black text-sm shadow-sm flex-shrink-0">
                                {initials}
                              </div>
                              <div className="flex flex-col text-left">
                                <span className="font-black text-slate-800 text-sm">
                                  {sub.usuario.nombres} {sub.usuario.apellidos || ''}
                                </span>
                                <span className="text-[10px] text-slate-400 font-bold mt-0.5">{sub.usuario.correo}</span>
                              </div>
                            </div>
                          </td>

                          {/* Plan Contratado */}
                          <td className="px-6 py-4.5 align-middle">
                            <div className="flex flex-col items-start gap-1">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-[9px] font-extrabold border uppercase tracking-wide ${getPlanBadgeColor(sub.plan_code)}`}>
                                {sub.plan_name}
                              </span>
                              <span className="text-[9px] text-slate-400 font-bold flex items-center gap-1 mt-0.5 text-left">
                                <CreditCard className="w-3 h-3 text-slate-300" />
                                {sub.pago_metodo} · {sub.moneda} {parseFloat(sub.monto).toFixed(2)} (Ref: {sub.referencia})
                              </span>
                            </div>
                          </td>

                          {/* Fecha Inicio */}
                          <td className="px-6 py-4.5 align-middle">
                            <span className="text-slate-600 text-xs font-bold">
                              {sub.fecha_inicio ? new Date(sub.fecha_inicio).toLocaleDateString() : 'N/A'}
                            </span>
                          </td>

                          {/* Fecha Vencimiento */}
                          <td className="px-6 py-4.5 align-middle">
                            <span className={`text-xs font-bold flex items-center gap-1.5 ${sub.estado === 'ACTIVO' ? 'text-slate-700' : 'text-rose-500 font-black'}`}>
                              <Calendar className="w-3.5 h-3.5 text-slate-400" />
                              {sub.fecha_vencimiento ? new Date(sub.fecha_vencimiento).toLocaleDateString() : 'N/A'}
                            </span>
                          </td>

                          {/* Estado */}
                          <td className="px-6 py-4.5 align-middle">
                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                              sub.estado === 'ACTIVO' 
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-100' 
                                : 'bg-rose-50 text-rose-700 border-rose-100'
                            }`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${
                                sub.estado === 'ACTIVO' ? 'bg-emerald-500' : 'bg-rose-500'
                              }`}></span>
                              {sub.estado}
                            </span>
                          </td>

                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Table Footer */}
          {!isLoading && filteredSubscribers.length > 0 && (
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-between items-center text-[10px] text-slate-400 font-bold uppercase tracking-wider">
              <span>Mostrando {filteredSubscribers.length} suscriptores</span>
            </div>
          )}

        </div>

        {/* Right Side: Plans Overview / Sidebar (col-span-1) */}
        <div className="lg:col-span-1 space-y-6">
          
          <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm text-left">
            <h3 className="text-xs font-black text-slate-900 uppercase tracking-widest border-b pb-2 mb-4">Planes activos</h3>
            
            <div className="space-y-4">
              {[
                { label: 'Plan Diario', count: dailyCount, color: 'border-slate-100 bg-slate-50 text-slate-800' },
                { label: 'Plan Mensual', count: monthlyCount, color: 'border-blue-100 bg-blue-50/40 text-blue-800' },
                { label: 'Plan Anual', count: annualCount, color: 'border-amber-100 bg-amber-50/40 text-amber-800' }
              ].map((item, idx) => (
                <div key={idx} className={`p-3 border rounded-xl flex items-center justify-between ${item.color}`}>
                  <span className="text-[11px] font-bold uppercase tracking-wide">{item.label}</span>
                  <span className="text-base font-black">{item.count}</span>
                </div>
              ))}
            </div>

            <div className="bg-emerald-50 border border-emerald-100/50 rounded-xl p-3.5 mt-5 flex gap-2 text-emerald-800 text-[10px] font-semibold leading-relaxed">
              <AlertCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>
                Los usuarios cuya suscripción está activa tienen acceso total a leer cualquier edición del periódico.
              </span>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};

export default Subscribers;
