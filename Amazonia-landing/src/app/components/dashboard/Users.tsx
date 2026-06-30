import React, { useState, useEffect, useRef } from 'react';
import { 
  Users as UsersIcon, UserPlus, Search, Filter, Shield, 
  Mail, MessageSquare, MoreVertical, CheckCircle, AlertTriangle, 
  Loader2, RefreshCw, X, Ban, Check, ShieldAlert, BadgeAlert
} from 'lucide-react';
import { useAuth } from '../../contexts/auth';
import api from '../../services/api';
import { toast } from 'sonner';

interface Member {
  id: number;
  usuario: {
    id: number;
    usr_correo: string;
    nombres: string;
    apellidos: string | null;
  };
  es_principal: boolean;
  fecha_asignacion: string;
  estado: 'ACTIVO' | 'SUSPENDIDO';
  motivo: string | null;
  roles: Array<{
    rol_codigo: string;
    rol_nombre: string;
    es_principal: boolean;
    estado: string;
  }>;
}

interface Invitation {
  id: number;
  email: string;
  rol_nombre?: string;
  role_code: string;
  estado: string;
  fecha_creacion: string;
}

const Users: React.FC = () => {
  const { activeCompanyId } = useAuth();
  
  // List states
  const [members, setMembers] = useState<Member[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'TODOS' | 'ACTIVO' | 'SUSPENDIDO'>('TODOS');
  
  // Modals state
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showSuspendModal, setShowSuspendModal] = useState(false);
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);
  
  // Form states
  const [inviteEmail, setInviteEmail] = useState('');
  const [invitePassword, setInvitePassword] = useState('');
  const [inviteRole, setInviteRole] = useState('EDITOR'); // SUPERADMIN, ADMIN_EMPRESA, EDITOR, LECTOR
  const [inviteMessage, setInviteMessage] = useState('');
  const [suspendReason, setSuspendReason] = useState('');
  
  // UI states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeDropdownId, setActiveDropdownId] = useState<number | null>(null);
  
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setActiveDropdownId(null);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  const fetchData = async () => {
    if (!activeCompanyId) return;
    setIsLoading(true);
    try {
      // 1. Fetch Company Members
      const membersRes = await api.get(`/companies/${activeCompanyId}/members/`);
      let membersList: Member[] = [];
      if (membersRes.data && Array.isArray(membersRes.data.results)) {
        membersList = membersRes.data.results;
      } else if (Array.isArray(membersRes.data)) {
        membersList = membersRes.data;
      }
      setMembers(membersList);

      // 2. Fetch Company Invitations (if endpoint exists)
      try {
        const inviteRes = await api.get(`/companies/${activeCompanyId}/invitations/`);
        // If paginated, get results array
        const inviteData = inviteRes.data?.results || inviteRes.data || [];
        setInvitations(inviteData);
      } catch (err) {
        console.warn("No se pudieron cargar las invitaciones, usando lista vacía:", err);
        setInvitations([]);
      }
    } catch (error) {
      console.error("Error al cargar usuarios de la empresa:", error);
      toast.error("Error al cargar la lista de usuarios");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeCompanyId]);

  // Invite/Create user submit handler
  const handleInviteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCompanyId || !inviteEmail || !invitePassword) {
      toast.error("Por favor completa los campos requeridos.");
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post(`/companies/${activeCompanyId}/members/create-direct/`, {
        email: inviteEmail,
        password: invitePassword,
        role_code: inviteRole
      });
      
      toast.success("¡Usuario creado con éxito!");
      setShowInviteModal(false);
      
      // Reset form
      setInviteEmail('');
      setInvitePassword('');
      setInviteRole('EDITOR');
      
      // Refresh list
      fetchData();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.response?.data?.email?.[0] || error.response?.data?.password?.[0] || "Error al crear el usuario.";
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Suspend member submit handler
  const handleSuspendSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCompanyId || !selectedMember || !suspendReason) return;

    setIsSubmitting(true);
    try {
      await api.post(`/companies/${activeCompanyId}/members/${selectedMember.id}/suspend/`, {
        motivo: suspendReason
      });
      
      toast.success(`Usuario ${selectedMember.usuario.nombres} suspendido.`);
      setShowSuspendModal(false);
      setSuspendReason('');
      setSelectedMember(null);
      fetchData();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || "No se pudo suspender al usuario.";
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Reactivate member handler
  const handleReactivateMember = async (member: Member) => {
    if (!activeCompanyId) return;
    
    setIsLoading(true);
    try {
      await api.post(`/companies/${activeCompanyId}/members/${member.id}/reactivate/`);
      toast.success(`Usuario ${member.usuario.nombres} reactivado con éxito.`);
      fetchData();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || "No se pudo reactivar al usuario.";
      toast.error(errorMsg);
      setIsLoading(false);
    }
  };

  const getRoleBadgeColor = (code: string) => {
    switch (code) {
      case 'SUPERADMIN':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'ADMIN_EMPRESA':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'EDITOR':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  const getInitials = (nombres: string, apellidos: string | null) => {
    const fLetter = nombres ? nombres.charAt(0) : '';
    const sLetter = apellidos ? apellidos.charAt(0) : '';
    return (fLetter + sLetter).toUpperCase() || 'U';
  };

  // Filter members locally by search and status
  const filteredMembers = members.filter(member => {
    const fullName = `${member.usuario.nombres} ${member.usuario.apellidos || ''}`.toLowerCase();
    const email = member.usuario.usr_correo.toLowerCase();
    const query = searchQuery.toLowerCase();
    
    const matchesSearch = fullName.includes(query) || email.includes(query);
    const matchesStatus = statusFilter === 'TODOS' || member.estado === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  // Calculate metrics
  const totalCount = members.length;
  const activeCount = members.filter(m => m.estado === 'ACTIVO').length;
  const suspendedCount = members.filter(m => m.estado === 'SUSPENDIDO').length;
  const pendingInvitesCount = invitations.filter(i => i.estado === 'PENDIENTE').length;

  return (
    <div className="max-w-[90rem] mx-auto space-y-8 animate-in fade-in duration-300 text-left">
      
      {/* Header section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200/60 pb-6">
        <div>
          <h1 className="text-2xl font-black text-slate-900 leading-tight">
            Gestión de usuarios
          </h1>
          <p className="text-xs text-slate-500 font-semibold mt-1.5">
            Administra los roles, accesos y permisos de los usuarios del sistema.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setShowInviteModal(true)}
            className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-bold text-white bg-[#ea580c] hover:bg-[#d44f0a] rounded-xl transition-all shadow-md shadow-orange-500/10 active:scale-[0.98] cursor-pointer"
          >
            <UserPlus className="w-4 h-4" /> Crear nuevo usuario
          </button>
        </div>
      </div>

      {/* Stats Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { title: 'Total Usuarios', value: totalCount, icon: UsersIcon, color: 'text-[#1a4d2e] bg-emerald-50' },
          { title: 'Usuarios Activos', value: activeCount, icon: Check, color: 'text-emerald-600 bg-emerald-50' },
          { title: 'Usuarios Suspendidos', value: suspendedCount, icon: Ban, color: 'text-rose-600 bg-rose-50' },
          { title: 'Invitaciones Pendientes', value: pendingInvitesCount, icon: Mail, color: 'text-blue-600 bg-blue-50' }
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

      {/* Main Grid: central table & list */}
      <div className="bg-white border border-slate-200 rounded-3xl shadow-sm overflow-hidden">
        
        {/* Table Filter Actions Bar */}
        <div className="p-5 border-b border-slate-200/80 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-50/50">
          {/* Tabs Filter */}
          <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200/60">
            {[
              { label: 'Todos', value: 'TODOS' },
              { label: 'Activos', value: 'ACTIVO' },
              { label: 'Suspendidos', value: 'SUSPENDIDO' }
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
                placeholder="Buscar por nombre o correo..."
                className="w-full bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-700 placeholder-slate-400 focus:outline-none focus:border-[#1a4d2e] transition-all font-semibold"
              />
            </div>
            <button 
              onClick={fetchData}
              className="p-2.5 border border-slate-200 rounded-xl bg-white text-slate-500 hover:text-slate-800 transition-colors shadow-sm cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Table Area */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                <th className="px-6 py-4">Usuario</th>
                <th className="px-6 py-4">Roles Asignados</th>
                <th className="px-6 py-4">Fecha de ingreso</th>
                <th className="px-6 py-4">Estado</th>
                <th className="px-6 py-4 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-xs font-semibold text-slate-700">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="py-24 text-center">
                    <div className="flex flex-col items-center justify-center gap-3">
                      <Loader2 className="w-8 h-8 text-[#1a4d2e] animate-spin" />
                      <span className="text-slate-400 font-bold text-sm">Cargando usuarios...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredMembers.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-24 text-center">
                    <div className="flex flex-col items-center justify-center gap-2 max-w-sm mx-auto text-slate-400">
                      <UsersIcon className="w-12 h-12 text-slate-300" />
                      <h4 className="font-bold text-slate-700 text-sm mt-2">No se encontraron usuarios</h4>
                      <p className="text-[11px] leading-relaxed text-center">No hay usuarios registrados que coincidan con la búsqueda.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredMembers.map((member) => {
                  const initials = getInitials(member.usuario.nombres, member.usuario.apellidos);
                  return (
                    <tr key={member.id} className="hover:bg-slate-50/40 transition-colors">
                      {/* Avatar y Datos Personales */}
                      <td className="px-6 py-4.5">
                        <div className="flex items-center gap-3.5">
                          <div className="w-10 h-10 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center text-[#1a4d2e] font-black text-sm shadow-sm flex-shrink-0">
                            {initials}
                          </div>
                          <div className="flex flex-col">
                            <span className="font-black text-slate-800 text-sm">
                              {member.usuario.nombres} {member.usuario.apellidos || ''}
                            </span>
                            <span className="text-[10px] text-slate-400 font-bold mt-0.5">{member.usuario.usr_correo}</span>
                          </div>
                        </div>
                      </td>

                      {/* Roles */}
                      <td className="px-6 py-4.5 align-middle">
                        <div className="flex flex-wrap gap-1.5">
                          {member.roles && member.roles.length > 0 ? (
                            member.roles.map((r, ri) => (
                              <span 
                                key={ri} 
                                className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[9px] font-extrabold border uppercase tracking-wide ${getRoleBadgeColor(r.rol_codigo)}`}
                              >
                                {r.rol_nombre}
                              </span>
                            ))
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-slate-400 text-[8px] font-extrabold">
                              SIN ROL
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Fecha Asignación */}
                      <td className="px-6 py-4.5 align-middle">
                        <span className="text-slate-600 text-xs font-bold">
                          {member.fecha_asignacion ? new Date(member.fecha_asignacion).toLocaleDateString() : 'N/A'}
                        </span>
                      </td>

                      {/* Estado */}
                      <td className="px-6 py-4.5 align-middle">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                          member.estado === 'ACTIVO' 
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-100' 
                            : 'bg-rose-50 text-rose-700 border-rose-100'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${
                            member.estado === 'ACTIVO' ? 'bg-emerald-500' : 'bg-rose-500'
                          }`}></span>
                          {member.estado}
                        </span>
                      </td>

                      {/* Acciones */}
                      <td className="px-6 py-4.5 text-center align-middle relative">
                        <div className="flex items-center justify-center gap-2">
                          {member.estado === 'ACTIVO' ? (
                            <button
                              onClick={() => {
                                setSelectedMember(member);
                                setSuspendReason('');
                                setShowSuspendModal(true);
                              }}
                              disabled={member.es_principal}
                              title="Suspender acceso del usuario"
                              className={`p-1.5 border rounded-lg transition-colors flex items-center justify-center ${
                                member.es_principal 
                                  ? 'text-slate-300 border-slate-100 cursor-not-allowed'
                                  : 'text-rose-500 border-rose-100 hover:bg-rose-50 cursor-pointer'
                              }`}
                            >
                              <Ban className="w-3.5 h-3.5" />
                            </button>
                          ) : (
                            <button
                              onClick={() => handleReactivateMember(member)}
                              title="Reactivar acceso del usuario"
                              className="p-1.5 border border-emerald-100 rounded-lg text-emerald-600 hover:bg-emerald-50 transition-colors flex items-center justify-center cursor-pointer"
                            >
                              <Check className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Invitaciones Pendientes Card Section */}
        {invitations.length > 0 && (
          <div className="border-t border-slate-200 p-6 bg-slate-50/30 text-left">
            <h4 className="text-xs font-black text-slate-800 uppercase tracking-widest mb-4">Invitaciones pendientes</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {invitations
                .filter(inv => inv.estado === 'PENDIENTE')
                .map((invite) => (
                  <div key={invite.id} className="bg-white p-4 rounded-xl border border-slate-200 flex items-center justify-between shadow-sm">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className="w-8 h-8 rounded-lg bg-orange-50 border border-orange-100 flex items-center justify-center text-[#ea580c] flex-shrink-0">
                        <Mail className="w-4 h-4" />
                      </div>
                      <div className="flex flex-col overflow-hidden">
                        <span className="text-xs font-bold text-slate-800 truncate">{invite.email}</span>
                        <span className="text-[9px] text-slate-400 font-extrabold uppercase mt-0.5 tracking-wide">
                          Rol: {invite.role_code}
                        </span>
                      </div>
                    </div>
                    <span className="text-[8px] font-black uppercase text-orange-600 bg-orange-50 border border-orange-100 px-1.5 py-0.5 rounded">
                      Enviada
                    </span>
                  </div>
              ))}
            </div>
          </div>
        )}

      </div>

      {/* ======================================================== */}
      {/* CREATE NEW MEMBER MODAL                                  */}
      {/* ======================================================== */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-[#0b1f13]/50 backdrop-blur-sm" onClick={() => setShowInviteModal(false)}></div>
          <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-slate-100 z-10 p-6 animate-in zoom-in-95 duration-150 text-left max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 pb-4 mb-5">
              <div className="flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-[#ea580c]" />
                <h3 className="text-lg font-black text-slate-900">Crear usuario</h3>
              </div>
              <button 
                onClick={() => setShowInviteModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-full hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleInviteSubmit} className="space-y-4">
              {/* Correo / Usuario */}
              <div>
                <label className="block text-[10px] font-black text-slate-600 uppercase tracking-wide mb-1.5">
                  Usuario (Correo Electrónico)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                    <Mail className="w-4 h-4" />
                  </span>
                  <input
                    type="email"
                    required
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="correo@ejemplo.com"
                    className="w-full pl-9 pr-4 py-2.5 border border-slate-200 bg-slate-50/50 rounded-xl text-xs font-semibold focus:outline-none focus:border-[#1a4d2e]"
                  />
                </div>
              </div>

              {/* Contraseña */}
              <div>
                <label className="block text-[10px] font-black text-slate-600 uppercase tracking-wide mb-1.5">
                  Contraseña
                </label>
                <div className="relative">
                  <input
                    type="password"
                    required
                    value={invitePassword}
                    onChange={(e) => setInvitePassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-4 py-2.5 border border-slate-200 bg-slate-50/50 rounded-xl text-xs font-semibold focus:outline-none focus:border-[#1a4d2e]"
                  />
                </div>
              </div>

              {/* Rol */}
              <div>
                <label className="block text-[10px] font-black text-slate-600 uppercase tracking-wide mb-1.5">
                  Rol a Asignar
                </label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full border border-slate-200 bg-slate-50/50 rounded-xl p-2.5 text-xs font-semibold focus:outline-none focus:border-[#1a4d2e] text-slate-700"
                >
                  <option value="SUPERADMIN">Superadministrador de plataforma</option>
                  <option value="ADMIN_EMPRESA">Administrador del periódico</option>
                  <option value="EDITOR">Editor de contenido</option>
                  <option value="LECTOR">Lector de periódico</option>
                </select>
              </div>

              {/* Submit button */}
              <div className="flex gap-3 pt-4 border-t border-slate-100 mt-6">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-bold transition-all text-center cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 py-2.5 rounded-xl text-white bg-[#ea580c] hover:bg-[#d44f0a] text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-md shadow-orange-500/10 cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      Crear usuario
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* SUSPEND ACCESSS MODAL                                    */}
      {/* ======================================================== */}
      {showSuspendModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-[#0b1f13]/50 backdrop-blur-sm" onClick={() => setShowSuspendModal(false)}></div>
          <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-slate-100 z-10 p-6 animate-in zoom-in-95 duration-150 text-left max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 pb-4 mb-5">
              <div className="flex items-center gap-2">
                <Ban className="w-5 h-5 text-rose-600" />
                <h3 className="text-lg font-black text-slate-900">Suspender acceso</h3>
              </div>
              <button 
                onClick={() => setShowSuspendModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-full hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSuspendSubmit} className="space-y-4">
              <div className="bg-rose-50 border border-rose-100 rounded-xl p-3 flex gap-2 text-rose-700 text-[11px] leading-relaxed">
                <AlertTriangle className="w-4.5 h-4.5 text-rose-500 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold block mb-0.5">Atención</span>
                  El usuario <strong>{selectedMember?.usuario.nombres}</strong> perderá temporalmente el acceso de edición e inicio de sesión asignado a esta empresa hasta que sea reactivado.
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-black text-slate-600 uppercase tracking-wide mb-1.5">
                  Motivo de la Suspensión
                </label>
                <textarea
                  required
                  value={suspendReason}
                  onChange={(e) => setSuspendReason(e.target.value)}
                  placeholder="Especifica el motivo de la suspensión administrativa..."
                  rows={3}
                  className="w-full px-3 py-2 border border-slate-200 bg-slate-50/50 rounded-xl text-xs font-semibold focus:outline-none focus:border-rose-500 resize-none"
                />
              </div>

              {/* Submit button */}
              <div className="flex gap-3 pt-4 border-t border-slate-100 mt-6">
                <button
                  type="button"
                  onClick={() => setShowSuspendModal(false)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-bold transition-all text-center cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 py-2.5 rounded-xl text-white bg-rose-600 hover:bg-rose-700 text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-md shadow-rose-500/10 cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      Confirmar Suspensión
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default Users;
