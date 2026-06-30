import React from 'react';
import { 
  Newspaper, Calendar, Crown, Check, CheckCircle2, 
  Star, Lock, Zap, Monitor, Headphones 
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/auth';
import { toast } from 'sonner';

export function PricingSection() {
  const { isAuthenticated, openAuthModal } = useAuth();
  const navigate = useNavigate();

  const handlePlanClick = (planName: string, price: string, planCode: string) => {
    if (!isAuthenticated) {
      toast.info(`Para adquirir el ${planName}, por favor inicia sesión o crea una cuenta primero.`);
      openAuthModal('register');
    } else {
      toast.success(`Redirigiendo a la pasarela de pago para el ${planName}...`);
      navigate(`/payment?plan=${planCode}`);
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

        {/* Pricing Cards Grid */}
        <div className="grid md:grid-cols-3 gap-8 items-stretch mb-16 text-left max-w-6xl mx-auto">
          
          {/* Card 1: PLAN DIARIO */}
          <div className="border border-slate-200 rounded-2xl p-8 bg-white shadow-sm hover:shadow-md transition-shadow duration-300 flex flex-col justify-between relative">
            <div>
              {/* Icon & Title */}
              <div className="flex flex-col items-center text-center mb-6">
                <div className="w-12 h-12 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center mb-3">
                  <Newspaper size={22} className="text-[#1a4d2e]" />
                </div>
                <h3 className="text-sm font-extrabold tracking-wider text-[#1a4d2e] uppercase mb-1">PLAN DIARIO</h3>
                <p className="text-xs text-gray-500 font-medium">Ideal para informarte cada día</p>
              </div>

              {/* Price */}
              <div className="text-center mb-6">
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-xl font-bold text-slate-800">S/</span>
                  <span className="text-5xl font-black text-[#1a4d2e]">0.50</span>
                </div>
                <p className="text-xs text-gray-400 mt-1">por edición</p>
              </div>

              {/* Checklist */}
              <ul className="space-y-3.5 mb-8">
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 size={18} className="text-emerald-600 flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-600 font-medium">Acceso a la edición del día</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 size={18} className="text-emerald-600 flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-600 font-medium">Lectura en línea</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 size={18} className="text-emerald-600 flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-600 font-medium">Desde cualquier dispositivo</span>
                </li>
              </ul>
            </div>

            {/* Button */}
            <button 
              onClick={() => handlePlanClick('Plan Diario', '0.50', 'diario')}
              className="w-full py-3.5 px-4 rounded-xl text-white font-bold bg-[#1a4d2e] hover:bg-[#153e25] transition-colors flex items-center justify-center gap-2 shadow-sm active:scale-[0.98] duration-150 cursor-pointer"
            >
              <Newspaper size={18} />
              Comprar ahora
            </button>
          </div>

          {/* Card 2: PLAN MENSUAL (Featured) */}
          <div className="border-2 border-[#ea580c] rounded-2xl p-8 bg-white shadow-md hover:shadow-lg transition-shadow duration-300 flex flex-col justify-between relative">
            <div className="absolute -top-3.5 right-6 bg-[#ea580c] text-white px-4 py-1 rounded-full text-[10px] font-black uppercase tracking-wider shadow-sm">
              Más popular
            </div>
            <div>
              {/* Icon & Title */}
              <div className="flex flex-col items-center text-center mb-6">
                <div className="w-12 h-12 rounded-full bg-orange-50 border border-orange-100 flex items-center justify-center mb-3">
                  <Calendar size={22} className="text-[#ea580c]" />
                </div>
                <h3 className="text-sm font-extrabold tracking-wider text-[#ea580c] uppercase mb-1">PLAN MENSUAL</h3>
                <p className="text-xs text-gray-500 font-medium">Para lectores frecuentes</p>
              </div>

              {/* Price */}
              <div className="text-center mb-6">
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-xl font-bold text-slate-800">S/</span>
                  <span className="text-5xl font-black text-slate-800">14.50</span>
                </div>
                <p className="text-xs text-gray-400 mt-1">por mes</p>
              </div>

              {/* Checklist */}
              <ul className="space-y-3.5 mb-8">
                <li className="flex items-center gap-2.5">
                  <Check size={18} className="text-[#ea580c] stroke-[3px] flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-600 font-semibold">Acceso completo a todas las ediciones</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check size={18} className="text-[#ea580c] stroke-[3px] flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-600 font-semibold">Historial de ediciones</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check size={18} className="text-[#ea580c] stroke-[3px] flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-600 font-semibold">Lectura sin límites</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check size={18} className="text-[#ea580c] stroke-[3px] flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-600 font-semibold">Desde cualquier dispositivo</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check size={18} className="text-[#ea580c] stroke-[3px] flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-600 font-semibold">Soporte prioritario</span>
                </li>
              </ul>
            </div>

            {/* Button */}
            <button 
              onClick={() => handlePlanClick('Plan Mensual', '14.50', 'mensual')}
              className="w-full py-3.5 px-4 rounded-xl text-white font-bold bg-[#ea580c] hover:bg-[#d44f0a] transition-colors flex items-center justify-center gap-2 shadow-sm active:scale-[0.98] duration-150 cursor-pointer"
            >
              <Star size={18} className="fill-white text-transparent" />
              Suscribirme ahora
            </button>
          </div>

          {/* Card 3: PLAN ANUAL */}
          <div className="border border-slate-200 rounded-2xl p-8 bg-white shadow-sm hover:shadow-md transition-shadow duration-300 flex flex-col justify-between relative">
            <div>
              {/* Icon & Title */}
              <div className="flex flex-col items-center text-center mb-6">
                <div className="w-12 h-12 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center mb-3">
                  <Crown size={22} className="text-[#1a4d2e]" />
                </div>
                <h3 className="text-sm font-extrabold tracking-wider text-[#1a4d2e] uppercase mb-1">PLAN ANUAL</h3>
                <p className="text-xs text-gray-500 font-medium">La mejor opción para ti</p>
              </div>

              {/* Price */}
              <div className="text-center mb-6">
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-xl font-bold text-slate-800">S/</span>
                  <span className="text-5xl font-black text-[#1a4d2e]">129.00</span>
                </div>
                <p className="text-xs text-gray-400 mt-1">por año</p>
              </div>

              {/* Checklist */}
              <ul className="space-y-3.5 mb-8">
                <li className="flex items-center gap-2.5">
                  <Check size={18} className="text-emerald-600 stroke-[3px] flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-600 font-medium">Acceso completo a todas las ediciones</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check size={18} className="text-emerald-600 stroke-[3px] flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-600 font-medium">Historial de ediciones</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check size={18} className="text-emerald-600 stroke-[3px] flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-600 font-medium">Lectura sin límites</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check size={18} className="text-emerald-600 stroke-[3px] flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-600 font-medium">Desde cualquier dispositivo</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check size={18} className="text-emerald-600 stroke-[3px] flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-600 font-medium">Soporte prioritario</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <CheckCircle2 size={18} className="text-emerald-600 flex-shrink-0" />
                  <span className="text-xs md:text-sm text-slate-800 font-black">2 meses gratis</span>
                </li>
              </ul>
            </div>

            {/* Button */}
            <button 
              onClick={() => handlePlanClick('Plan Anual', '129.00', 'anual')}
              className="w-full py-3.5 px-4 rounded-xl text-white font-bold bg-[#1a4d2e] hover:bg-[#153e25] transition-colors flex items-center justify-center gap-2 shadow-sm active:scale-[0.98] duration-150 cursor-pointer"
            >
              <Crown size={18} />
              Suscribirme ahora
            </button>
          </div>

        </div>

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

