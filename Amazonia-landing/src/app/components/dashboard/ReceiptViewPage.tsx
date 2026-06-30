import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, Download, RefreshCw, Mail, ShieldCheck, 
  Calendar, CreditCard, ChevronRight, User, AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../../services/api';
import logoAmazonia from '../../../imports/logo_amazonia.png';

interface PurchaseDetails {
  id: number;
  edicion?: {
    edi_id: number;
    titulo: string;
    fecha_edicion: string;
    precio: string;
    moneda: string;
  };
  fecha_creacion: string;
  fecha_confirmacion: string | null;
  estado: string;
  monto_total: string;
  moneda: string;
  medio_pago?: string;
  identificador_externo?: string;
  usuario?: {
    nombres: string;
    apellidos: string | null;
    correo: string;
    id: number;
  };
}

export const ReceiptViewPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const purchaseId = searchParams.get('id');

  const [purchase, setPurchase] = useState<PurchaseDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isResending, setIsResending] = useState(false);

  useEffect(() => {
    const fetchReceipt = async () => {
      if (!purchaseId) {
        setIsLoading(false);
        return;
      }
      try {
        const res = await api.get(`my-purchases/?id=${purchaseId}`);
        setPurchase(res.data);
      } catch (err: any) {
        console.error(err);
        toast.error("No se pudo cargar la información del comprobante.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchReceipt();
  }, [purchaseId]);

  const handlePrint = () => {
    window.print();
  };

  const handleResendEmail = async () => {
    if (!purchaseId) return;
    setIsResending(true);
    try {
      // Re-trigger email notification
      await api.post(`payments/mock-confirm/`, {
        com_id: Number(purchaseId)
      });
      toast.success("Comprobante enviado nuevamente a tu correo.");
    } catch (err) {
      console.error(err);
      toast.error("Error al reenviar el comprobante.");
    } finally {
      setIsResending(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 text-[#1a4d2e] animate-spin" />
          <span className="text-xs font-bold text-slate-500">Cargando comprobante...</span>
        </div>
      </div>
    );
  }

  if (!purchase) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 text-left">
        <div className="max-w-md w-full bg-white p-8 rounded-3xl border border-slate-200 shadow-lg text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
          <h2 className="text-lg font-black text-slate-900">Comprobante no encontrado</h2>
          <p className="text-xs text-slate-500 font-semibold leading-relaxed">
            No se ha podido localizar el comprobante de compra o no tienes los permisos necesarios para visualizarlo.
          </p>
          <button 
            onClick={() => navigate('/dashboard')}
            className="px-5 py-2.5 rounded-xl bg-[#1a4d2e] hover:bg-[#153e25] text-white font-bold text-xs transition-colors cursor-pointer"
          >
            Volver al Dashboard
          </button>
        </div>
      </div>
    );
  }

  const formattedId = String(purchase.id).padStart(6, '0');
  const userFullName = purchase.usuario 
    ? `${purchase.usuario.nombres} ${purchase.usuario.apellidos || ''}`.trim()
    : 'Lector Registrado';
  
  // Format date display
  const dateObj = purchase.fecha_confirmacion ? new Date(purchase.fecha_confirmacion) : new Date(purchase.fecha_creacion);
  const formattedDate = dateObj.toLocaleDateString('es-PE', { day: '2-digit', month: 'long', year: 'numeric' });
  const formattedTime = dateObj.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', hour12: true });

  // Plan info extraction
  const refUpper = (purchase.identificador_externo || '').toUpperCase();
  let planName = "Plan Mensual";
  let planPeriod = "1 mes";
  let durationDesc = "1 mes";

  if (refUpper.includes("DIARIO") || (purchase.edicion && purchase.monto_total === '0.50')) {
    planName = "Plan Diario";
    planPeriod = "1 día";
    durationDesc = "1 día (Edición de hoy)";
  } else if (refUpper.includes("ANUAL") || (purchase.edicion && purchase.monto_total === '129.00')) {
    planName = "Plan Anual";
    planPeriod = "12 meses";
    durationDesc = "12 meses (2 meses de regalo)";
  } else if (purchase.edicion) {
    planName = `Edición Digital: ${purchase.edicion.titulo}`;
    planPeriod = "Permanente";
    durationDesc = "Acceso permanente a esta edición";
  }

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 sm:px-6 relative flex flex-col justify-between antialiased text-slate-800">
      <style>{`
        @media print {
          body {
            background: white !important;
            padding: 0 !important;
          }
          .no-print {
            display: none !important;
          }
          .print-card {
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
          }
        }
      `}</style>

      {/* Main receipt container */}
      <div className="max-w-2xl w-full mx-auto bg-white rounded-3xl border border-slate-200 shadow-xl p-6 sm:p-10 space-y-6 print-card text-left">
        
        {/* Header section */}
        <div className="flex flex-row justify-between items-start gap-4 pb-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-brand-500 rounded-xl flex items-center justify-center shadow-md">
              <img src={logoAmazonia} alt="Amazonia" className="w-6 h-6 object-contain" />
            </div>
            <div className="flex flex-col">
              <span className="text-base font-black text-[#1a4d2e] tracking-tight leading-none">Amazonia Diario</span>
              <span className="text-[9px] font-bold text-slate-400 mt-1 uppercase tracking-wider">Información que conecta nuestra región</span>
            </div>
          </div>

          <div className="text-right">
            <span className="px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-200">
              Aprobada
            </span>
            <div className="text-xs font-black text-slate-900 mt-2">
              N° DE COMPROBANTE: <span className="text-slate-500 font-bold">CMP-{formattedId}</span>
            </div>
            <div className="text-[10px] text-slate-400 font-bold mt-1">
              {formattedDate} &bull; {formattedTime}
            </div>
          </div>
        </div>

        {/* Hero approved block */}
        <div className="bg-emerald-50/50 border border-emerald-100 rounded-2xl p-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-800 flex-shrink-0">
            <ShieldCheck size={20} />
          </div>
          <div>
            <h4 className="text-xs font-black text-slate-900 leading-snug">¡Tu compra ha sido aprobada!</h4>
            <p className="text-[10px] text-slate-500 leading-relaxed font-bold mt-0.5">
              Hemos validado tu pago correctamente y tu suscripción ya está activa. Disfruta de todos los beneficios de tu plan.
            </p>
          </div>
        </div>

        {/* General Info Grid */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-1.5">
            <User size={13} />
            <span>Información General</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3.5 text-xs">
            <div className="space-y-1">
              <span className="text-slate-400 font-bold block">Nombre:</span>
              <span className="text-slate-900 font-black">{userFullName}</span>
            </div>
            <div className="space-y-1">
              <span className="text-slate-400 font-bold block">Correo electrónico:</span>
              <span className="text-slate-900 font-black">{purchase.usuario?.correo}</span>
            </div>
            <div className="space-y-1">
              <span className="text-slate-400 font-bold block">Plan contratado:</span>
              <span className="text-slate-900 font-black">{planName}</span>
            </div>
            <div className="space-y-1">
              <span className="text-slate-400 font-bold block">Período:</span>
              <span className="text-slate-900 font-black">{durationDesc}</span>
            </div>
            <div className="space-y-1">
              <span className="text-slate-400 font-bold block">Método de pago:</span>
              <span className="text-slate-900 font-black capitalize">{purchase.medio_pago || 'YAPE'}</span>
            </div>
            <div className="space-y-1">
              <span className="text-slate-400 font-bold block">Código de referencia:</span>
              <span className="text-slate-900 font-black">{purchase.identificador_externo || purchase.id}</span>
            </div>
          </div>
        </div>

        {/* Resumen Tabla */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-1.5">
            <CreditCard size={13} />
            <span>Resumen de la Compra</span>
          </div>

          <div className="overflow-x-auto border border-slate-200 rounded-xl">
            <table className="w-full border-collapse text-xs text-left">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="p-3 font-black text-slate-500 uppercase tracking-wider text-[9px]">Concepto</th>
                  <th className="p-3 font-black text-slate-500 uppercase tracking-wider text-[9px]">Descripción</th>
                  <th className="p-3 font-black text-slate-500 uppercase tracking-wider text-[9px]">Detalle</th>
                  <th className="p-3 font-black text-slate-500 uppercase tracking-wider text-[9px] text-right">Importe</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-150">
                <tr>
                  <td className="p-3 font-black text-slate-800">Plan contratado</td>
                  <td className="p-3 text-slate-500 font-semibold">Acceso y suscripción</td>
                  <td className="p-3 text-slate-500 font-bold">{planName}</td>
                  <td className="p-3 font-black text-slate-900 text-right">S/ {purchase.monto_total}</td>
                </tr>
                <tr>
                  <td className="p-3 font-black text-slate-800">Método de pago</td>
                  <td className="p-3 text-slate-500 font-semibold">Pago digital verificado</td>
                  <td className="p-3 text-slate-500 font-bold capitalize">{purchase.medio_pago || 'YAPE'}</td>
                  <td className="p-3 text-slate-400 font-semibold text-right">-</td>
                </tr>
                <tr>
                  <td className="p-3 font-black text-slate-800">Período</td>
                  <td className="p-3 text-slate-500 font-semibold">Vigencia del plan</td>
                  <td className="p-3 text-slate-500 font-bold">{planPeriod}</td>
                  <td className="p-3 text-slate-400 font-semibold text-right">-</td>
                </tr>
                <tr className="bg-slate-50/50">
                  <td colSpan={3} className="p-3 font-black text-slate-600 text-right uppercase tracking-wider text-[9px]">Total Pagado</td>
                  <td className="p-3 font-black text-[#ea580c] text-sm text-right">S/ {purchase.monto_total}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer Support Info */}
        <div className="border-t border-slate-100 pt-5 text-center space-y-2">
          <p className="text-[11px] font-black text-[#1a4d2e]">Gracias por confiar en Amazonia Diario ❤️</p>
          <div className="flex flex-wrap justify-center gap-x-6 gap-y-1.5 text-[9px] font-bold text-slate-400">
            <span>soporte@amazoniadiario.com</span>
            <span>+51 987 654 321</span>
            <span>www.amazoniadiario.com</span>
          </div>
        </div>

      </div>

      {/* Action buttons (hidden on print) */}
      <div className="max-w-2xl w-full mx-auto mt-6 flex flex-col sm:flex-row gap-3 no-print">
        <button 
          onClick={handlePrint}
          className="flex-1 py-3 px-5 rounded-xl bg-[#1a4d2e] hover:bg-[#153e25] text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors cursor-pointer shadow-md"
        >
          <Download size={14} /> Descargar PDF
        </button>

        <button 
          onClick={handleResendEmail}
          disabled={isResending}
          className="flex-1 py-3 px-5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
        >
          {isResending ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Mail size={14} />}
          Enviar por correo de nuevo
        </button>

        <Link 
          to="/dashboard"
          className="flex-1 py-3 px-5 rounded-xl bg-slate-100 border border-slate-200 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
        >
          <ArrowLeft size={14} /> Volver a mi Cuenta
        </Link>
      </div>

    </div>
  );
};
