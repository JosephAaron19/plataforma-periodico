import React, { useState, useEffect, useRef } from 'react';
import { 
  CreditCard, Search, Calendar, Download, Eye, 
  CheckCircle2, XCircle, AlertTriangle, Loader2, ArrowRight,
  Landmark, QrCode, ShieldCheck, X, ArrowLeft, RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../../services/api';

interface Purchase {
  id: string;
  usuario: {
    nombre: string;
    email: string;
    iniciales: string;
    color: string;
  };
  plan: {
    nombre: string;
    precioDetalle: string;
    duracionTexto: string;
  };
  monto: string;
  metodo: {
    tipo: 'yape' | 'plin' | 'banco_bcp' | 'banco_bbva';
    nombre: string;
    detalle: string;
  };
  fecha: string;
  estado: 'PENDIENTE' | 'APROBADO' | 'RECHAZADO';
  comprobanteUrl: string;
  motivoRechazo?: string;
  notaUsuario?: string;
  observacionRechazo?: string;
}

// SVG Logos for Yape and Plin
const YapeLogo: React.FC<{ className?: string }> = ({ className = "w-6 h-6" }) => (
  <svg className={className} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="48" fill="#74227E" />
    <path d="M30 65C32 50 40 32 52 32C65 32 70 42 70 52C70 65 58 72 45 72C38 72 32 68 30 65Z" fill="#00D2C4" />
    <path d="M42 42C44 38 48 35 52 35C57 35 60 38 60 42C60 47 55 52 48 56" stroke="white" strokeWidth="6" strokeLinecap="round" />
    <circle cx="48" cy="65" r="4" fill="white" />
  </svg>
);

const PlinLogo: React.FC<{ className?: string }> = ({ className = "w-6 h-6" }) => (
  <svg className={className} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="48" fill="#00B1C9" />
    <path d="M32 30H68V38H54V70H46V38H32V30Z" fill="white" />
    <circle cx="62" cy="62" r="8" fill="#FF7900" />
  </svg>
);

// Voucher Screen mockup styled with extreme realism (Highly compact to avoid scroll)
const VoucherMockup: React.FC<{ method: string, amount: string, name: string, date: string }> = ({ method, amount, name, date }) => {
  const isYape = method.toLowerCase() === 'yape';
  const isPlin = method.toLowerCase() === 'plin';

  return (
    <div className="w-[210px] border border-slate-200 rounded-2xl bg-slate-900 overflow-hidden shadow-md font-sans text-left text-[10px] text-white pb-3.5">
      {/* Top phone bar mockup (Ultra compact) */}
      <div className="px-3.5 pt-1.5 pb-1 flex justify-between items-center text-[7px] opacity-60 font-semibold select-none">
        <span>9:41</span>
        <div className="flex gap-1 items-center">
          <span className="w-1.5 h-1.5 bg-white rounded-full"></span>
          <span className="w-2.5 h-1.5 bg-white rounded-sm"></span>
        </div>
      </div>
      
      {/* Wallet Brand Header */}
      <div className="flex flex-col items-center py-2.5 space-y-0.5">
        {isYape ? (
          <div className="flex flex-col items-center">
            <YapeLogo className="w-7 h-7" />
            <span className="text-[12px] font-black tracking-tight mt-0.5">yape</span>
          </div>
        ) : isPlin ? (
          <div className="flex flex-col items-center">
            <PlinLogo className="w-7 h-7" />
            <span className="text-[12px] font-black tracking-tight mt-0.5">plin</span>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="w-7 h-7 bg-slate-800 rounded-full flex items-center justify-center text-slate-350 border border-slate-700">
              <Landmark size={13} />
            </div>
            <span className="text-[10px] font-black tracking-wider uppercase mt-1">{method}</span>
          </div>
        )}
      </div>

      {/* Voucher white box content */}
      <div className="mx-3 bg-white text-slate-800 rounded-xl p-3.5 space-y-3">
        <div className="text-center pb-2 border-b border-slate-100">
          <span className="text-[17px] font-black text-slate-950 block">{amount}</span>
          <span className="text-[9px] font-bold text-emerald-600 uppercase tracking-wide block mt-0.5">
            {isYape ? '¡Yapeaste el servicio!' : isPlin ? '¡Plineaste con éxito!' : '¡Transferencia Exitosa!'}
          </span>
        </div>

        <div className="space-y-2 text-[8.5px] font-semibold text-slate-600">
          <div className="flex flex-col">
            <span className="text-[7px] text-slate-400 font-bold uppercase tracking-wider">Destino</span>
            <span className="text-slate-850 font-black">Amazonia Diario S.A.C.</span>
            <span className="text-[8px] text-slate-400 font-bold leading-none mt-0.5">987 654 321</span>
          </div>
          
          <div className="flex justify-between border-t border-slate-50 pt-1.5">
            <div className="flex flex-col">
              <span className="text-[7px] text-slate-400 font-bold uppercase tracking-wider">Fecha y hora</span>
              <span className="text-slate-800 font-bold">{date}</span>
            </div>
          </div>

          <div className="flex justify-between border-t border-slate-50 pt-1.5">
            <div className="flex flex-col">
              <span className="text-[7px] text-slate-400 font-bold uppercase tracking-wider">N° de operación</span>
              <span className="text-slate-800 font-bold font-mono">0123456789</span>
            </div>
          </div>

          <div className="flex flex-col border-t border-slate-50 pt-1.5">
            <span className="text-[7px] text-slate-400 font-bold uppercase tracking-wider">Desde</span>
            <span className="text-slate-850 font-black">{name}</span>
            <span className="text-[8px] text-slate-400 font-bold leading-none mt-0.5">987 654 321</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const Purchases: React.FC = () => {
  // Mapper function to transform backend items to Purchases UI interface
  const mapBackendToPurchase = (item: any): Purchase => {
    const isYape = item.pago.medio_pago?.toLowerCase() === 'yape';
    const isPlin = item.pago.medio_pago?.toLowerCase() === 'plin';
    const methodType = isYape ? 'yape' : isPlin ? 'plin' : 'banco_bcp';
    const methodName = item.pago.medio_pago || 'Yape';

    // Format plan details
    let planName = 'Plan Mensual';
    let planPriceDetail = 'S/ 14.50 / mes';
    let planDuration = '1 mes';

    if (item.plan_code === 'diario') {
      planName = 'Plan Diario';
      planPriceDetail = 'S/ 0.50 / edición';
      planDuration = '1 día';
    } else if (item.plan_code === 'anual') {
      planName = 'Plan Anual';
      planPriceDetail = 'S/ 129.00 / año';
      planDuration = '12 meses';
    } else if (item.plan_code.startsWith('edition_')) {
      planName = 'Edición Digital';
      planPriceDetail = `S/ ${item.monto}`;
      planDuration = 'Acceso Permanente';
    }

    // Initials & Colors
    const names = item.usuario.nombres || 'Lector';
    const iniciales = names.split(' ').map((n: any) => n[0]).join('').substring(0, 2).toUpperCase();
    const colors = [
      'bg-orange-100 text-orange-700',
      'bg-emerald-100 text-emerald-700',
      'bg-blue-100 text-blue-700',
      'bg-purple-100 text-purple-700'
    ];
    const color = colors[item.usuario.id % colors.length];

    // Dates
    const dateObj = new Date(item.fecha_creacion);
    const formattedDate = dateObj.toLocaleDateString('es-PE', { day: '2-digit', month: 'long', year: 'numeric' }) + 
      ' - ' + dateObj.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', hour12: true });

    // States
    let status: 'PENDIENTE' | 'APROBADO' | 'RECHAZADO' = 'PENDIENTE';
    if (item.estado === 'PAGADA') status = 'APROBADO';
    else if (item.estado === 'RECHAZADA') status = 'RECHAZADO';

    return {
      id: `#CMP-${String(item.com_id).padStart(6, '0')}`,
      usuario: {
        nombre: `${item.usuario.nombres} ${item.usuario.apellidos || ''}`.trim(),
        email: item.usuario.correo,
        iniciales,
        color
      },
      plan: {
        nombre: planName,
        precioDetalle: planPriceDetail,
        duracionTexto: planDuration
      },
      monto: `S/ ${item.monto}`,
      metodo: {
        tipo: methodType,
        nombre: methodName,
        detalle: item.pago.identificador_externo || '987 654 321'
      },
      fecha: formattedDate,
      estado: status,
      comprobanteUrl: item.pago.comprobante_url || ''
    };
  };

  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchPurchases = async () => {
    setIsLoading(true);
    try {
      const res = await api.get('admin/pending/?status=todos');
      const mapped = res.data.map(mapBackendToPurchase);
      setPurchases(mapped);
    } catch (err) {
      console.error(err);
      toast.error("No se pudo cargar la lista de compras del backend.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPurchases();
  }, []);

  // View modes: 'list' | 'detail' | 'reject'
  const [viewMode, setViewMode] = useState<'list' | 'detail' | 'reject'>('list');
  const [selectedPurchase, setSelectedPurchase] = useState<Purchase | null>(null);

  // Filters state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('todos');
  const [methodFilter, setMethodFilter] = useState<string>('todos');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // Reject view states (matching exact mockup form fields)
  const [selectedReason, setSelectedReason] = useState('Comprobante no válido');
  const [observationText, setObservationText] = useState('El comprobante enviado está borroso y no se puede leer correctamente.');
  const [isProcessing, setIsProcessing] = useState(false);

  // Popup Approval States (Auto close in 4 seconds or click outside)
  const [showApprovalPopup, setShowApprovalPopup] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Clean timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  // Filter list
  const filteredPurchases = purchases.filter((item) => {
    const matchesSearch = 
      item.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.usuario.nombre.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.usuario.email.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'todos' || item.estado.toLowerCase() === statusFilter.toLowerCase();

    const matchesMethod = 
      methodFilter === 'todos' || 
      (methodFilter === 'yape' && item.metodo.tipo === 'yape') ||
      (methodFilter === 'plin' && item.metodo.tipo === 'plin') ||
      (methodFilter === 'banco' && item.metodo.tipo.startsWith('banco_'));

    return matchesSearch && matchesStatus && matchesMethod;
  });

  // Action handlers
  const handleOpenDetail = (purchase: Purchase) => {
    setSelectedPurchase(purchase);
    setViewMode('detail');
  };

  const handleApprovePayment = async () => {
    if (!selectedPurchase) return;
    setIsProcessing(true);
    
    try {
      const comId = parseInt(selectedPurchase.id.replace('#CMP-', ''), 10);
      
      // Call convalidation endpoint in backend
      await api.post('admin/validate/', {
        com_id: comId,
        action: 'approve'
      });
      
      // Update in local state
      setPurchases(prev => prev.map(p => 
        p.id === selectedPurchase.id ? { ...p, estado: 'APROBADO', motivoRechazo: undefined, observacionRechazo: undefined } : p
      ));
      
      setSelectedPurchase(prev => prev ? { ...prev, estado: 'APROBADO', motivoRechazo: undefined, observacionRechazo: undefined } : null);
      
      // Open approval popup modal
      setShowApprovalPopup(true);

      // Start 4-seconds auto close timer
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        handleCloseApprovalPopup();
      }, 4000);
      
      toast.success("Pago verificado y aprobado con éxito.");
    } catch (err: any) {
      console.error(err);
      const detail = err.response?.data?.detail || "Error al aprobar la compra.";
      toast.error(detail);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCloseApprovalPopup = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setShowApprovalPopup(false);
    setViewMode('list');
  };

  // Submit reject action (Matches mockup Confirmar)
  const handleConfirmReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPurchase) return;
    setIsProcessing(true);

    try {
      const comId = parseInt(selectedPurchase.id.replace('#CMP-', ''), 10);
      
      // Call convalidation endpoint in backend with reject action
      await api.post('admin/validate/', {
        com_id: comId,
        action: 'reject'
      });

      setPurchases(prev => prev.map(p => 
        p.id === selectedPurchase.id 
          ? { ...p, estado: 'RECHAZADO', motivoRechazo: selectedReason, observacionRechazo: observationText } 
          : p
      ));

      toast.error(`Pago de la compra ${selectedPurchase.id} rechazado.`);
      setViewMode('list');
    } catch (err: any) {
      console.error(err);
      const detail = err.response?.data?.detail || "Error al rechazar el pago.";
      toast.error(detail);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExportData = () => {
    toast.success("Listado de compras exportado a Excel de manera exitosa.");
  };

  return (
    <div className="space-y-5 text-left max-w-6xl w-full mx-auto p-2">
      
      {viewMode === 'list' && (
        /* ========================================================================= */
        /* VIEW 1: PURCHASES LIST TABLE                                              */
        /* ========================================================================= */
        <>
          {/* Title Header */}
          <div>
            <h2 className="text-xl font-black text-slate-900 leading-tight">Compras y Suscripciones</h2>
            <p className="text-xs text-slate-500 font-semibold mt-0.5">
              Gestiona y valida los pagos realizados por los usuarios
            </p>
          </div>

          {/* Filters Row */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-4 flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[200px]">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                <Search className="w-4 h-4" />
              </span>
              <input
                type="text"
                placeholder="Buscar por nombre, email o ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:border-[#1a4d2e] bg-slate-50/50"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-slate-200 rounded-xl p-2 text-xs font-semibold focus:outline-none focus:border-[#1a4d2e] bg-white text-slate-700 cursor-pointer min-w-[130px]"
            >
              <option value="todos">Todos los estados</option>
              <option value="pendiente">Pendiente</option>
              <option value="aprobado">Aprobado</option>
              <option value="rechazado">Rechazado</option>
            </select>

            <select
              value={methodFilter}
              onChange={(e) => setMethodFilter(e.target.value)}
              className="border border-slate-200 rounded-xl p-2 text-xs font-semibold focus:outline-none focus:border-[#1a4d2e] bg-white text-slate-700 cursor-pointer min-w-[140px]"
            >
              <option value="todos">Todos los métodos</option>
              <option value="yape">Yape</option>
              <option value="plin">Plin</option>
              <option value="banco">Transferencia Bancaria</option>
            </select>

            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Desde"
                onFocus={(e) => (e.target.type = 'date')}
                onBlur={(e) => (e.target.type = 'text')}
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold focus:outline-none focus:border-[#1a4d2e] bg-white text-slate-700 w-28"
              />
              <input
                type="text"
                placeholder="Hasta"
                onFocus={(e) => (e.target.type = 'date')}
                onBlur={(e) => (e.target.type = 'text')}
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold focus:outline-none focus:border-[#1a4d2e] bg-white text-slate-700 w-28"
              />
            </div>

            <button
              onClick={handleExportData}
              className="ml-auto inline-flex items-center gap-1.5 px-4 py-2 border border-slate-200 rounded-xl hover:bg-slate-50 text-xs font-bold text-slate-700 transition-all shadow-sm cursor-pointer"
            >
              <Download size={14} /> Exportar
            </button>
          </div>

          {/* Table Container */}
          <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] border-collapse text-left text-xs font-semibold text-slate-700">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/50 uppercase text-[9px] font-black tracking-wider text-slate-400">
                    <th className="py-4 px-6 select-none">ID Compra</th>
                    <th className="py-4 px-4 select-none">Usuario</th>
                    <th className="py-4 px-4 select-none">Plan</th>
                    <th className="py-4 px-4 select-none">Monto</th>
                    <th className="py-4 px-4 select-none">Método de pago</th>
                    <th className="py-4 px-4 select-none">Fecha de pago</th>
                    <th className="py-4 px-4 select-none">Estado</th>
                    <th className="py-4 px-6 text-center select-none">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {isLoading ? (
                    <tr>
                      <td colSpan={8} className="py-12 text-center text-slate-400 text-xs font-bold">
                        <div className="flex flex-col items-center justify-center gap-2">
                          <Loader2 className="w-6 h-6 animate-spin text-[#1a4d2e]" />
                          <span>Cargando transacciones desde el servidor...</span>
                        </div>
                      </td>
                    </tr>
                  ) : filteredPurchases.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-12 text-center text-slate-400 text-xs font-bold">
                        No se encontraron compras o suscripciones registradas.
                      </td>
                    </tr>
                  ) : (
                    filteredPurchases.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-50/30 transition-colors">
                        <td className="py-4 px-6 font-bold text-slate-500 font-mono">
                          {item.id}
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-black text-xs shadow-sm flex-shrink-0 ${item.usuario.color}`}>
                              {item.usuario.iniciales}
                            </div>
                            <div className="flex flex-col">
                              <span className="font-bold text-slate-900 leading-snug">{item.usuario.nombre}</span>
                              <span className="text-[10px] text-slate-400 font-semibold">{item.usuario.email}</span>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex flex-col">
                            <span className="font-bold text-slate-900 leading-snug">{item.plan.nombre}</span>
                            <span className="text-[10px] text-slate-400 font-bold">{item.plan.precioDetalle}</span>
                          </div>
                        </td>
                        <td className="py-4 px-4 font-bold text-slate-900">
                          {item.monto}
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-2.5">
                            <div className="flex-shrink-0">
                              {item.metodo.tipo === 'yape' ? (
                                <YapeLogo className="w-7 h-7" />
                              ) : item.metodo.tipo === 'plin' ? (
                                <PlinLogo className="w-7 h-7" />
                              ) : (
                                <div className="w-7 h-7 bg-slate-100 rounded-full flex items-center justify-center text-slate-500 border border-slate-200">
                                  <Landmark size={14} />
                                </div>
                              )}
                            </div>
                            <div className="flex flex-col text-left">
                              <span className="font-bold text-slate-800 leading-none">{item.metodo.nombre}</span>
                              <span className="text-[10px] text-slate-400 font-bold mt-1 leading-none">{item.metodo.detalle}</span>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <span>{item.fecha}</span>
                        </td>
                        <td className="py-4 px-4">
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider ${
                            item.estado === 'APROBADO' 
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                              : item.estado === 'RECHAZADO'
                              ? 'bg-rose-50 text-rose-700 border border-rose-100'
                              : 'bg-amber-50 text-amber-700 border border-amber-100'
                          }`}>
                            {item.estado === 'PENDIENTE' ? 'Pendiente' : item.estado === 'APROBADO' ? 'Aprobado' : 'Rechazado'}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-center">
                          <button
                            onClick={() => handleOpenDetail(item)}
                            className="p-1.5 rounded-lg border border-slate-200 hover:border-slate-400 text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-all cursor-pointer"
                          >
                            <Eye size={13.5} />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Footer */}
            <div className="bg-slate-50/50 border-t border-slate-100 px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-bold text-slate-500">
              <span>Mostrando 1 a {filteredPurchases.length} de {filteredPurchases.length} compras</span>
              
              <div className="flex items-center gap-1.5">
                <button className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-400 hover:text-slate-600 disabled:opacity-40" disabled>
                  &lt;
                </button>
                <button className="px-3 py-1.5 rounded-lg bg-[#1a4d2e] text-white shadow shadow-[#1a4d2e]/10">1</button>
                <button className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600">2</button>
                <button className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600">3</button>
                <span className="px-1 text-slate-400 select-none">...</span>
                <button className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600">13</button>
                <button className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-400 hover:text-slate-600">
                  &gt;
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {viewMode === 'detail' && selectedPurchase && (
        /* ========================================================================= */
        /* VIEW 2: PURCHASE COMPREHENSIVE DETAIL                                     */
        /* ========================================================================= */
        <div className="space-y-4 animate-in fade-in duration-200 text-left">
          
          {/* Upper Action Bar */}
          <div className="flex items-center justify-between border-b border-slate-250 pb-2.5">
            <button 
              onClick={() => setViewMode('list')}
              className="inline-flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-slate-900 border border-slate-200 bg-white hover:bg-slate-50 px-3.5 py-1.5 rounded-xl transition-all cursor-pointer shadow-sm leading-none"
            >
              <ArrowLeft size={13} /> Volver al listado
            </button>
            
            <button 
              onClick={() => toast.info("Historial de auditoría cargando...")}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-slate-900 border border-slate-200 bg-white hover:bg-slate-50 px-3.5 py-1.5 rounded-xl transition-all cursor-pointer shadow-sm leading-none"
            >
              <RefreshCw size={12} /> Historial de estados
            </button>
          </div>

          {/* Split layout */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
            
            {/* Left Column: Purchase Details & User Notes */}
            <div className="lg:col-span-7 flex flex-col gap-4">
              
              {/* Information container */}
              <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-4 text-xs font-semibold text-slate-600 space-y-3">
                <h3 className="text-xs font-black text-slate-900 pb-2 border-b border-slate-100 uppercase tracking-wider text-[11px] select-none leading-none">
                  Información de la compra
                </h3>
                
                <div className="space-y-2.5 pt-1">
                  {/* ID */}
                  <div className="flex items-center py-1.5 border-b border-slate-50">
                    <span className="w-1/3 text-slate-400 font-bold uppercase tracking-wider text-[9px]">ID Compra</span>
                    <span className="w-2/3 text-slate-900 font-black font-mono">{selectedPurchase.id}</span>
                  </div>

                  {/* Usuario */}
                  <div className="flex items-center py-1.5 border-b border-slate-50">
                    <span className="w-1/3 text-slate-400 font-bold uppercase tracking-wider text-[9px]">Usuario</span>
                    <div className="w-2/3 flex items-center gap-2.5">
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center font-black text-xs shadow-sm flex-shrink-0 ${selectedPurchase.usuario.color}`}>
                        {selectedPurchase.usuario.iniciales}
                      </div>
                      <div className="flex flex-col">
                        <span className="font-bold text-slate-900 leading-tight">{selectedPurchase.usuario.nombre}</span>
                        <span className="text-[9px] text-slate-400 font-semibold leading-none">{selectedPurchase.usuario.email}</span>
                      </div>
                    </div>
                  </div>

                  {/* Plan */}
                  <div className="flex items-center py-1.5 border-b border-slate-50">
                    <span className="w-1/3 text-slate-400 font-bold uppercase tracking-wider text-[9px]">Plan</span>
                    <div className="w-2/3 flex flex-col">
                      <span className="font-black text-slate-900 leading-none">{selectedPurchase.plan.nombre}</span>
                      <span className="text-[9px] text-slate-400 font-bold mt-1 leading-none">{selectedPurchase.plan.precioDetalle}</span>
                    </div>
                  </div>

                  {/* Monto */}
                  <div className="flex items-center py-1.5 border-b border-slate-50">
                    <span className="w-1/3 text-slate-400 font-bold uppercase tracking-wider text-[9px]">Monto</span>
                    <span className="w-2/3 text-slate-950 font-black text-xs">{selectedPurchase.monto}</span>
                  </div>

                  {/* Método */}
                  <div className="flex items-center py-1.5 border-b border-slate-50">
                    <span className="w-1/3 text-slate-400 font-bold uppercase tracking-wider text-[9px]">Método de pago</span>
                    <div className="w-2/3 flex items-center gap-2">
                      <div className="flex-shrink-0">
                        {selectedPurchase.metodo.tipo === 'yape' ? (
                          <YapeLogo className="w-6 h-6" />
                        ) : selectedPurchase.metodo.tipo === 'plin' ? (
                          <PlinLogo className="w-6 h-6" />
                        ) : (
                          <div className="w-6 h-6 bg-slate-100 rounded-full flex items-center justify-center text-slate-550 border border-slate-200">
                            <Landmark size={12} />
                          </div>
                        )}
                      </div>
                      <div className="flex flex-col text-left">
                        <span className="font-bold text-slate-800 leading-none">{selectedPurchase.metodo.nombre}</span>
                        <span className="text-[9px] text-slate-400 font-bold mt-0.5 leading-none">{selectedPurchase.metodo.detalle}</span>
                      </div>
                    </div>
                  </div>

                  {/* Fecha */}
                  <div className="flex items-center py-1.5 border-b border-slate-50">
                    <span className="w-1/3 text-slate-400 font-bold uppercase tracking-wider text-[9px]">Fecha de pago</span>
                    <span className="w-2/3 text-slate-900 font-bold">{selectedPurchase.fecha}</span>
                  </div>

                  {/* Estado actual */}
                  <div className="flex items-center py-1.5">
                    <span className="w-1/3 text-slate-400 font-bold uppercase tracking-wider text-[9px]">Estado actual</span>
                    <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider ${
                      selectedPurchase.estado === 'APROBADO' 
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                        : selectedPurchase.estado === 'RECHAZADO'
                        ? 'bg-rose-50 text-rose-700 border border-rose-100'
                        : 'bg-amber-50 text-amber-700 border border-amber-100'
                    }`}>
                      {selectedPurchase.estado === 'PENDIENTE' ? 'Pendiente' : selectedPurchase.estado === 'APROBADO' ? 'Aprobado' : 'Rechazado'}
                    </span>
                  </div>
                </div>
              </div>

              {/* User Notes Box */}
              <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-4 text-xs font-semibold text-slate-600">
                <h3 className="text-xs font-black text-slate-900 pb-1.5 border-b border-slate-100 uppercase tracking-wider text-[11px] select-none leading-none">
                  Notas del usuario (opcional)
                </h3>
                <p className="text-slate-700 font-semibold leading-relaxed pt-2.5 px-1 text-xs">
                  {selectedPurchase.notaUsuario || "El usuario no incluyó notas adicionales para esta transacción."}
                </p>
              </div>

            </div>

            {/* Right Column: Voucher verification */}
            <div className="lg:col-span-5 flex flex-col justify-between gap-4">
              
              {/* Comprobante Image container */}
              <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-4 flex flex-col items-center justify-between gap-3">
                <h3 className="text-xs font-black text-slate-900 w-full pb-2 border-b border-slate-100 uppercase tracking-wider text-[11px] select-none leading-none">
                  Comprobante de pago
                </h3>
                
                {/* Real Comprobante Image or Phone Voucher rendering */}
                <div className="bg-slate-50 border border-slate-150 rounded-2xl p-2 flex items-center justify-center w-full min-h-[300px] overflow-hidden">
                  {selectedPurchase.comprobanteUrl ? (
                    <img 
                      src={selectedPurchase.comprobanteUrl} 
                      alt="Comprobante de Pago" 
                      className="max-h-[380px] object-contain rounded-lg border border-slate-200" 
                    />
                  ) : (
                    <VoucherMockup 
                      method={selectedPurchase.metodo.nombre}
                      amount={selectedPurchase.monto}
                      name={selectedPurchase.usuario.nombre}
                      date={selectedPurchase.fecha}
                    />
                  )}
                </div>

                {/* Download image button */}
                <button
                  type="button"
                  onClick={() => {
                    if (selectedPurchase.comprobanteUrl) {
                      window.open(selectedPurchase.comprobanteUrl, '_blank');
                    } else {
                      toast.info("No hay una imagen física asociada a este comprobante simulado.");
                    }
                  }}
                  className="w-full py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-600 font-bold text-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-sm"
                >
                  Ver / Descargar imagen <Download size={12} />
                </button>
              </div>

              {/* Action buttons */}
              <div className="space-y-3">
                {selectedPurchase.estado === 'PENDIENTE' ? (
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setViewMode('reject')}
                      className="w-full py-2.5 rounded-xl border border-rose-200 bg-white text-rose-600 hover:bg-rose-50/50 text-xs font-black transition-all text-center cursor-pointer shadow-sm active:scale-[0.98]"
                    >
                      Rechazar compra
                    </button>
                    <button
                      type="button"
                      onClick={handleApprovePayment}
                      disabled={isProcessing}
                      className="w-full py-2.5 rounded-xl text-white bg-[#1a4d2e] hover:bg-[#133821] text-xs font-black transition-all flex items-center justify-center gap-1.5 shadow-md shadow-brand-500/10 cursor-pointer disabled:opacity-50 active:scale-[0.98]"
                    >
                      {isProcessing ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>Aprobar compra</>
                      )}
                    </button>
                  </div>
                ) : (
                  <div className={`p-3 rounded-2xl border flex items-center gap-2 text-xs font-black uppercase tracking-wider ${
                    selectedPurchase.estado === 'APROBADO'
                      ? 'bg-emerald-50 border-emerald-100 text-emerald-700 shadow-sm'
                      : 'bg-rose-50 border-rose-100 text-rose-700 shadow-sm'
                  }`}>
                    <CheckCircle2 size={14} />
                    <span>
                      Transacción validada como {selectedPurchase.estado.toLowerCase()}
                      {selectedPurchase.estado === 'RECHAZADO' && selectedPurchase.motivoRechazo && (
                        <span className="block text-[9px] font-bold text-rose-500 mt-1 capitalize leading-none normal-case">
                          Motivo: {selectedPurchase.motivoRechazo} {selectedPurchase.observacionRechazo && ` - ${selectedPurchase.observacionRechazo}`}
                        </span>
                      )}
                    </span>
                  </div>
                )}
              </div>

            </div>

          </div>

        </div>
      )}

      {viewMode === 'reject' && selectedPurchase && (
        /* ========================================================================= */
        /* VIEW 3: REJECT PURCHASE FORM                                              */
        /* ========================================================================= */
        <form onSubmit={handleConfirmReject} className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm max-w-xl mx-auto space-y-4 animate-in zoom-in-95 duration-150 text-left">
          
          <div className="border-b border-slate-100 pb-2.5">
            <h3 className="text-sm font-black text-slate-900 leading-none">
              Rechazar compra - {selectedPurchase.id}
            </h3>
          </div>

          <div className="bg-rose-50/50 border border-rose-100 rounded-2xl p-4 flex items-start gap-3 text-xs text-rose-700">
            <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <h4 className="font-black leading-snug">¿Estás seguro de rechazar esta compra?</h4>
              <p className="text-[10px] text-rose-600/80 font-bold leading-relaxed">
                El usuario será notificado y deberá realizar un nuevo pago.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="text-xs font-black text-slate-800 uppercase tracking-wider text-[10px] select-none leading-none">
              Motivo del rechazo
            </h4>

            <div className="space-y-1.5">
              <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                Selecciona el motivo
              </label>
              <select
                value={selectedReason}
                onChange={(e) => setSelectedReason(e.target.value)}
                className="w-full border border-slate-200 rounded-xl p-2.5 text-xs font-semibold focus:outline-none focus:border-rose-500 bg-white text-slate-700 cursor-pointer"
              >
                <option value="Comprobante no válido">Comprobante no válido</option>
                <option value="Monto incorrecto">Monto incorrecto</option>
                <option value="Comprobante duplicado">Comprobante duplicado</option>
                <option value="Imagen ilegible">Imagen ilegible</option>
                <option value="Otro">Otro motivo</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                Observación (opcional)
              </label>
              <div className="relative">
                <textarea
                  maxLength={200}
                  rows={3}
                  value={observationText}
                  onChange={(e) => setObservationText(e.target.value)}
                  placeholder="Detalles sobre el rechazo del pago..."
                  className="w-full p-3 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:border-rose-500 bg-slate-50/50 resize-none text-slate-800"
                />
                <span className="absolute bottom-2.5 right-3.5 text-[9px] font-bold text-slate-400">
                  {observationText.length}/200
                </span>
              </div>
            </div>
          </div>

          <div className="flex gap-4 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setViewMode('detail')}
              className="w-1/2 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-655 font-bold text-xs transition-all text-center cursor-pointer shadow-sm"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isProcessing}
              className="w-1/2 py-2.5 rounded-xl text-white bg-rose-600 hover:bg-rose-700 text-xs font-black transition-all flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50 shadow-md shadow-rose-600/10 active:scale-[0.98]"
            >
              {isProcessing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>Confirmar rechazo</>
              )}
            </button>
          </div>
        </form>
      )}

      {/* ========================================================================= */
      /* APPROVAL POPUP MODAL (Auto closes in 4 seconds or click outside backdrop)   */
      /* ========================================================================= */ }
      {showApprovalPopup && selectedPurchase && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-in fade-in duration-250 bg-[#0f172a]/40 backdrop-blur-sm"
          onClick={handleCloseApprovalPopup}
        >
          {/* Modal Content (Stops propagation to allow clicking outside to close) */}
          <div 
            className="relative w-full max-w-md bg-white rounded-3xl border border-slate-100 p-6 text-center space-y-4 shadow-2xl animate-in zoom-in-95 duration-200 text-slate-800"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="border-b border-slate-100 pb-2">
              <h3 className="text-xs font-black text-slate-900 uppercase tracking-wider leading-none">
                Aprobar compra - {selectedPurchase.id}
              </h3>
            </div>

            {/* Checkmark in Green circle with Confetti simulation */}
            <div className="relative w-16 h-16 mx-auto flex items-center justify-center">
              {/* Confetti simulation (Decorative points of color) */}
              <span className="absolute w-1.5 h-1.5 bg-rose-400 rounded-full top-1 left-2 animate-bounce"></span>
              <span className="absolute w-1.5 h-1.5 bg-emerald-400 rounded-full top-0 right-3 animate-ping"></span>
              <span className="absolute w-1.5 h-1.5 bg-purple-400 rounded-full bottom-2 left-0"></span>
              <span className="absolute w-2 h-2 bg-amber-400 rounded-full bottom-1 right-2"></span>
              <span className="absolute w-1 h-1 bg-cyan-400 rounded-full top-4 right-1"></span>

              <div className="w-12 h-12 bg-emerald-700 rounded-full flex items-center justify-center text-white shadow-md shadow-brand-500/10">
                <CheckCircle2 className="w-7 h-7" />
              </div>
            </div>

            {/* Text description */}
            <div className="space-y-1">
              <h4 className="text-sm font-black text-slate-950">¿Confirmar aprobación?</h4>
              <p className="text-[11px] text-slate-500 font-semibold leading-relaxed">
                El usuario recibirá acceso al plan <strong className="text-slate-800 font-bold">{selectedPurchase.plan.nombre}</strong> por un período de {selectedPurchase.plan.duracionTexto}.
              </p>
            </div>

            {/* Gray Detail list box */}
            <div className="bg-slate-50 border border-slate-100 rounded-2xl p-4 text-left space-y-2.5 text-[11px] font-semibold text-slate-600">
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-bold text-[9px] uppercase tracking-wider">Usuario</span>
                <span className="text-slate-850 font-black">{selectedPurchase.usuario.nombre}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-bold text-[9px] uppercase tracking-wider">Plan</span>
                <span className="text-slate-850 font-black">{selectedPurchase.plan.nombre}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-bold text-[9px] uppercase tracking-wider">Monto</span>
                <span className="text-slate-850 font-black">{selectedPurchase.monto}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-bold text-[9px] uppercase tracking-wider">Método de pago</span>
                <div className="flex items-center gap-1.5">
                  {selectedPurchase.metodo.tipo === 'yape' ? (
                    <YapeLogo className="w-4.5 h-4.5" />
                  ) : selectedPurchase.metodo.tipo === 'plin' ? (
                    <PlinLogo className="w-4.5 h-4.5" />
                  ) : (
                    <Landmark size={11} className="text-slate-450" />
                  )}
                  <span className="text-slate-850 font-black">{selectedPurchase.metodo.nombre} - {selectedPurchase.metodo.detalle}</span>
                </div>
              </div>
            </div>
            
          </div>
        </div>
      )}

    </div>
  );
};

export default Purchases;
