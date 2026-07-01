import React, { useState, useEffect } from 'react';
import { 
  Newspaper, Calendar, Crown, Check, CheckCircle2, 
  Star, Lock, Zap, Monitor, Headphones 
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/auth';
import { toast } from 'sonner';
import api from '../services/api';

interface PlanFuncionalidad {
  codigo_funcionalidad: string;
  nombre: string;
  descripcion: string | null;
  habilitada: boolean;
}

interface Plan {
  codigo: string;
  nombre: string;
  descripcion: string | null;
  precio: string;
  moneda: string;
  periodicidad: string;
  limite_usuarios: number | null;
  limite_ediciones_mes: number | null;
  limite_storage_mb: number | null;
  limite_pdf_mb: number | null;
  limite_paginas_pdf: number | null;
  es_publico: boolean;
  orden: number;
  estado: string;
  funcionalidades?: PlanFuncionalidad[];
}

export function PricingSection() {
  const { isAuthenticated, openAuthModal } = useAuth();
  const navigate = useNavigate();

  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const response = await api.get('/plans/');
        // The /plans/ endpoint already filters active and public, ordered by orden
        setPlans(response.data || []);
      } catch (error) {
        console.error("Error fetching plans from API, using fallback data:", error);
        loadFallbackPlans();
      } finally {
        setLoading(false);
      }
    };
    fetchPlans();
  }, []);

  const loadFallbackPlans = () => {
    setPlans([
      {
        codigo: "PLAN_DIARIO",
        nombre: "Plan Diario",
        descripcion: "Ideal para informarte cada día",
        precio: "0.50",
        moneda: "PEN",
        periodicidad: "PERSONALIZADO",
        limite_usuarios: 1,
        limite_ediciones_mes: 30,
        limite_storage_mb: 100,
        limite_pdf_mb: 20,
        limite_paginas_pdf: 50,
        es_publico: true,
        orden: 1,
        estado: "ACTIVO",
        funcionalidades: [
          { codigo_funcionalidad: "FEAT_ACCESO_DIA", nombre: "Acceso a la edición del día", descripcion: null, habilitada: true },
          { codigo_funcionalidad: "FEAT_LECTURA_LINEA", nombre: "Lectura en línea", descripcion: null, habilitada: true },
          { codigo_funcionalidad: "FEAT_MULTIDISPOSITIVO", nombre: "Desde cualquier dispositivo", descripcion: null, habilitada: true }
        ]
      },
      {
        codigo: "PLAN_MENSUAL",
        nombre: "Plan Mensual",
        descripcion: "Para lectores frecuentes",
        precio: "14.50",
        moneda: "PEN",
        periodicidad: "MENSUAL",
        limite_usuarios: 5,
        limite_ediciones_mes: 150,
        limite_storage_mb: 1024,
        limite_pdf_mb: 50,
        limite_paginas_pdf: 100,
        es_publico: true,
        orden: 2,
        estado: "ACTIVO",
        funcionalidades: [
          { codigo_funcionalidad: "FEAT_ACCESO_COMPLETO", nombre: "Acceso completo a todas las ediciones", descripcion: null, habilitada: true },
          { codigo_funcionalidad: "FEAT_HISTORIAL", nombre: "Historial de ediciones", descripcion: null, habilitada: true },
          { codigo_funcionalidad: "FEAT_LECTURA_ILIMITADA", nombre: "Lectura sin límites", descripcion: null, habilitada: true },
          { codigo_funcionalidad: "FEAT_MULTIDISPOSITIVO", nombre: "Desde cualquier dispositivo", descripcion: null, habilitada: true },
          { codigo_funcionalidad: "FEAT_SOPORTE_PRIO", nombre: "Soporte prioritario", descripcion: null, habilitada: true }
        ]
      },
      {
        codigo: "PLAN_ANUAL",
        nombre: "Plan Anual",
        descripcion: "La mejor opción para ti",
        precio: "129.00",
        moneda: "PEN",
        periodicidad: "ANUAL",
        limite_usuarios: 10,
        limite_ediciones_mes: 1000,
        limite_storage_mb: 10240,
        limite_pdf_mb: 100,
        limite_paginas_pdf: 200,
        es_publico: true,
        orden: 3,
        estado: "ACTIVO",
        funcionalidades: [
          { codigo_funcionalidad: "FEAT_ACCESO_COMPLETO", nombre: "Acceso completo a todas las ediciones", descripcion: null, habilitada: true },
          { codigo_funcionalidad: "FEAT_HISTORIAL", nombre: "Historial de ediciones", descripcion: null, habilitada: true },
          { codigo_funcionalidad: "FEAT_LECTURA_ILIMITADA", nombre: "Lectura sin límites", descripcion: null, habilitada: true },
          { codigo_funcionalidad: "FEAT_MULTIDISPOSITIVO", nombre: "Desde cualquier dispositivo", descripcion: null, habilitada: true },
          { codigo_funcionalidad: "FEAT_SOPORTE_PRIO", nombre: "Soporte prioritario", descripcion: null, habilitada: true },
          { codigo_funcionalidad: "FEAT_PROMO_GRATIS", nombre: "2 meses gratis", descripcion: null, habilitada: true }
        ]
      }
    ]);
  };

  const handlePlanClick = (planName: string, price: string, planCode: string) => {
    if (!isAuthenticated) {
      toast.info(`Para adquirir el ${planName}, por favor inicia sesión o crea una cuenta primero.`);
      openAuthModal('register');
    } else {
      toast.success(`Redirigiendo a la pasarela de pago para el ${planName}...`);
      // Use clean plan code (e.g. 'diario', 'mensual', 'anual') or code itself
      const routedCode = planCode.toLowerCase().replace('plan_', '');
      navigate(`/payment?plan=${routedCode}`);
    }
  };

  const getPeriodLabel = (periodicidad: string) => {
    switch (periodicidad.toUpperCase()) {
      case 'PERSONALIZADO':
        return 'por edición';
      case 'MENSUAL':
        return 'por mes';
      case 'ANUAL':
        return 'por año';
      case 'SEMESTRAL':
        return 'por semestral';
      case 'UNICO':
        return 'pago único';
      default:
        return `por ${periodicidad.toLowerCase()}`;
    }
  };

  return (
    <section id="planes" className="py-16 px-6 bg-white border-t border-gray-100">
      <div className="max-w-7xl mx-auto text-center">
        {/* Header */}
        <h2 className="text-4xl md:text-5xl font-extrabold mb-4 select-none">
          <span className="text-[#1a4d2e]">Elige </span>
          <span className="text-[#ea580c]">tu plan</span>
        </h2>
        <p className="text-gray-600 max-w-2xl mx-auto mb-16 text-sm md:text-base font-medium">
          Accede a todas nuestras ediciones digitales y mantente informado donde estés.
        </p>

        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-600"></div>
          </div>
        ) : (
          <div className={`grid items-stretch mb-16 text-left w-full ${
            plans.length === 1 ? 'max-w-md mx-auto grid-cols-1' :
            plans.length === 2 ? 'max-w-4xl mx-auto md:grid-cols-2 gap-6' :
            plans.length === 3 ? 'max-w-6xl mx-auto md:grid-cols-3 gap-6' :
            'max-w-[90rem] mx-auto md:grid-cols-2 lg:grid-cols-4 gap-4'
          }`}>
            {plans.map((plan) => {
              const isFeatured = plan.codigo.toUpperCase() === 'PLAN_MENSUAL';
              const showCompact = plans.length >= 4;
              
              // Icon Selection
              let PlanIcon = Newspaper;
              if (plan.codigo.toUpperCase() === 'PLAN_MENSUAL') PlanIcon = Calendar;
              else if (plan.codigo.toUpperCase() === 'PLAN_ANUAL') PlanIcon = Crown;

              return (
                <div 
                  key={plan.codigo}
                  className={`rounded-2xl bg-white flex flex-col justify-between relative transition-all duration-300 ${
                    showCompact ? 'p-5 md:p-6' : 'p-8'
                  } ${
                    isFeatured 
                      ? 'border-2 border-[#ea580c] shadow-md hover:shadow-lg' 
                      : 'border border-slate-200 shadow-sm hover:shadow-md'
                  }`}
                >
                  {isFeatured && (
                    <div className="absolute -top-3.5 right-6 bg-[#ea580c] text-white px-4 py-1 rounded-full text-[10px] font-black uppercase tracking-wider shadow-sm animate-pulse">
                      Más popular
                    </div>
                  )}

                  <div>
                    {/* Icon & Title */}
                    <div className="flex flex-col items-center text-center mb-6">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-3 border ${
                        isFeatured 
                          ? 'bg-orange-50 border-orange-100' 
                          : 'bg-emerald-50 border-emerald-100'
                      }`}>
                        <PlanIcon size={22} className={isFeatured ? 'text-[#ea580c]' : 'text-[#1a4d2e]'} />
                      </div>
                      <h3 className={`text-sm font-extrabold tracking-wider uppercase mb-1 ${
                        isFeatured ? 'text-[#ea580c]' : 'text-[#1a4d2e]'
                      }`}>
                        {plan.nombre}
                      </h3>
                      <p className="text-xs text-gray-500 font-medium leading-tight">{plan.descripcion || 'Acceso digital exclusivo'}</p>
                    </div>

                    {/* Price */}
                    <div className="text-center mb-6">
                      <div className="flex items-baseline justify-center gap-1">
                        <span className="text-xl font-bold text-slate-800">
                          {plan.moneda === 'PEN' ? 'S/' : '$'}
                        </span>
                        <span className={`font-black ${
                          showCompact ? 'text-3xl lg:text-4xl' : 'text-5xl'
                        } ${isFeatured ? 'text-slate-850' : 'text-[#1a4d2e]'}`}>
                          {Number(plan.precio).toFixed(2)}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">{getPeriodLabel(plan.periodicidad)}</p>
                    </div>

                    {/* Checklist */}
                    <ul className={`mb-8 ${showCompact ? 'space-y-2.5' : 'space-y-3.5'}`}>
                      {plan.funcionalidades && plan.funcionalidades.map((feat) => {
                        const isGratis = feat.nombre.toLowerCase().includes('gratis');
                        return (
                          <li key={feat.codigo_funcionalidad} className="flex items-start gap-2">
                            {isFeatured ? (
                              <Check size={16} className="text-[#ea580c] stroke-[3px] flex-shrink-0 mt-0.5" />
                            ) : isGratis ? (
                              <CheckCircle2 size={16} className="text-emerald-600 flex-shrink-0 mt-0.5" />
                            ) : (
                              <Check size={16} className="text-emerald-600 stroke-[3px] flex-shrink-0 mt-0.5" />
                            )}
                            <span className={`leading-tight ${
                              showCompact ? 'text-xs' : 'text-xs md:text-sm'
                            } ${
                              isGratis ? 'text-slate-850 font-black' : 'text-slate-600 font-semibold'
                            }`}>
                              {feat.nombre}
                            </span>
                          </li>
                        );
                      })}
                    </ul>
                  </div>

                  {/* Button */}
                  <button 
                    onClick={() => handlePlanClick(plan.nombre, plan.precio, plan.codigo)}
                    className={`w-full py-3.5 px-4 rounded-xl text-white font-bold transition-all flex items-center justify-center gap-2 shadow-sm active:scale-[0.98] duration-150 cursor-pointer ${
                      isFeatured 
                        ? 'bg-[#ea580c] hover:bg-[#d44f0a]' 
                        : 'bg-[#1a4d2e] hover:bg-[#153e25]'
                    }`}
                  >
                    {isFeatured ? (
                      <Star size={18} className="fill-white text-transparent" />
                    ) : plan.codigo.toUpperCase() === 'PLAN_DIARIO' ? (
                      <Newspaper size={18} />
                    ) : (
                      <Crown size={18} />
                    )}
                    {plan.codigo.toUpperCase() === 'PLAN_DIARIO' ? 'Comprar ahora' : 'Suscribirme ahora'}
                  </button>

                </div>
              );
            })}
          </div>
        )}

        {/* Features Bottom Bar */}
        <div className="bg-[#f8fafc] border border-slate-100 rounded-2xl py-6 px-4 md:px-8 max-w-6xl mx-auto flex flex-col md:flex-row gap-6 md:gap-0 justify-between items-stretch text-left">
          
          {/* Feature 1 */}
          <div className="flex-1 flex items-center gap-3.5 px-4 pb-6 md:pb-0 border-b md:border-b-0 md:border-r border-slate-200">
            <div className="w-10 h-10 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center flex-shrink-0">
              <Lock size={18} className="text-[#1a4d2e]" />
            </div>
            <div>
              <h4 className="text-xs font-black text-slate-800 mb-0.5">Pago seguro</h4>
              <p className="text-[10px] text-gray-500 font-medium leading-tight">Tus datos protegidos en todo momento</p>
            </div>
          </div>

          {/* Feature 2 */}
          <div className="flex-1 flex items-center gap-3.5 px-4 py-6 md:py-0 border-b md:border-b-0 md:border-r border-slate-200">
            <div className="w-10 h-10 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center flex-shrink-0">
              <Zap size={18} className="text-[#1a4d2e]" />
            </div>
            <div>
              <h4 className="text-xs font-black text-slate-800 mb-0.5">Acceso inmediato</h4>
              <p className="text-[10px] text-gray-500 font-medium leading-tight">Comienza a leer al instante después de tu compra</p>
            </div>
          </div>

          {/* Feature 3 */}
          <div className="flex-1 flex items-center gap-3.5 px-4 py-6 md:py-0 border-b md:border-b-0 md:border-r border-slate-200">
            <div className="w-10 h-10 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center flex-shrink-0">
              <Monitor size={18} className="text-[#1a4d2e]" />
            </div>
            <div>
              <h4 className="text-xs font-black text-slate-800 mb-0.5">Disponible 24/7</h4>
              <p className="text-[10px] text-gray-500 font-medium leading-tight">Lee cuando quieras, donde quieras</p>
            </div>
          </div>

          {/* Feature 4 */}
          <div className="flex-1 flex items-center gap-3.5 px-4 pt-6 md:pt-0">
            <div className="w-10 h-10 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center flex-shrink-0">
              <Headphones size={18} className="text-[#1a4d2e]" />
            </div>
            <div>
              <h4 className="text-xs font-black text-slate-800 mb-0.5">Soporte dedicado</h4>
              <p className="text-[10px] text-gray-500 font-medium leading-tight">Estamos aquí para ayudarte siempre</p>
            </div>
          </div>

        </div>

      </div>
    </section>
  );
}

export default PricingSection;
