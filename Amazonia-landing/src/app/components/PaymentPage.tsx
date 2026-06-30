import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, Check, Copy, Upload, ShieldCheck, Loader2, 
  Calendar, CreditCard, ChevronRight, Rocket, CheckCircle2,
  Smartphone, Landmark, QrCode, Lock
} from 'lucide-react';
import { toast } from 'sonner';
import logoAmazonia from '../../imports/logo_amazonia.png';
import api from '../services/api';

// SVG Logos for Yape and Plin
const YapeLogo: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
  <svg className={className} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="48" fill="#74227E" />
    <path d="M30 65C32 50 40 32 52 32C65 32 70 42 70 52C70 65 58 72 45 72C38 72 32 68 30 65Z" fill="#00D2C4" />
    <path d="M42 42C44 38 48 35 52 35C57 35 60 38 60 42C60 47 55 52 48 56" stroke="white" strokeWidth="6" strokeLinecap="round" />
    <circle cx="48" cy="65" r="4" fill="white" />
  </svg>
);

const PlinLogo: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
  <svg className={className} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="48" fill="#00B1C9" />
    <path d="M32 30H68V38H54V70H46V38H32V30Z" fill="white" />
    <circle cx="62" cy="62" r="8" fill="#FF7900" />
  </svg>
);

// Custom QR codes
const YapeQR: React.FC<{ className?: string }> = ({ className = "w-24 h-24" }) => (
  <svg className={className} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="5" y="5" width="25" height="25" stroke="white" strokeWidth="4" />
    <rect x="11" y="11" width="13" height="13" fill="white" />
    <rect x="70" y="5" width="25" height="25" stroke="white" strokeWidth="4" />
    <rect x="76" y="11" width="13" height="13" fill="white" />
    <rect x="5" y="70" width="25" height="25" stroke="white" strokeWidth="4" />
    <rect x="11" y="76" width="13" height="13" fill="white" />
    <rect x="40" y="8" width="8" height="8" fill="white" />
    <rect x="52" y="15" width="8" height="8" fill="white" />
    <rect x="40" y="24" width="8" height="8" fill="white" />
    <rect x="8" y="40" width="8" height="8" fill="white" />
    <rect x="20" y="48" width="8" height="8" fill="white" />
    <rect x="12" y="56" width="8" height="8" fill="white" />
    <rect x="44" y="44" width="12" height="12" fill="white" />
    <rect x="72" y="40" width="8" height="8" fill="white" />
    <rect x="84" y="48" width="8" height="8" fill="white" />
    <rect x="76" y="56" width="8" height="8" fill="white" />
    <rect x="40" y="72" width="8" height="8" fill="white" />
    <rect x="52" y="80" width="8" height="8" fill="white" />
    <rect x="44" y="88" width="8" height="8" fill="white" />
    <rect x="72" y="72" width="8" height="8" fill="white" />
    <rect x="84" y="80" width="8" height="8" fill="white" />
    <rect x="76" y="88" width="8" height="8" fill="white" />
    <rect x="42" y="42" width="16" height="16" rx="4" fill="#74227E" />
    <path d="M47 52C48 48 52 46 54 49C54 52 50 54 48 55" stroke="white" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const PlinQR: React.FC<{ className?: string }> = ({ className = "w-24 h-24" }) => (
  <svg className={className} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="5" y="5" width="25" height="25" stroke="white" strokeWidth="4" />
    <rect x="11" y="11" width="13" height="13" fill="white" />
    <rect x="70" y="5" width="25" height="25" stroke="white" strokeWidth="4" />
    <rect x="76" y="11" width="13" height="13" fill="white" />
    <rect x="5" y="70" width="25" height="25" stroke="white" strokeWidth="4" />
    <rect x="11" y="76" width="13" height="13" fill="white" />
    <rect x="40" y="8" width="8" height="8" fill="white" />
    <rect x="52" y="15" width="8" height="8" fill="white" />
    <rect x="40" y="24" width="8" height="8" fill="white" />
    <rect x="8" y="40" width="8" height="8" fill="white" />
    <rect x="20" y="48" width="8" height="8" fill="white" />
    <rect x="12" y="56" width="8" height="8" fill="white" />
    <rect x="44" y="44" width="12" height="12" fill="white" />
    <rect x="72" y="40" width="8" height="8" fill="white" />
    <rect x="84" y="48" width="8" height="8" fill="white" />
    <rect x="76" y="56" width="8" height="8" fill="white" />
    <rect x="40" y="72" width="8" height="8" fill="white" />
    <rect x="52" y="80" width="8" height="8" fill="white" />
    <rect x="44" y="88" width="8" height="8" fill="white" />
    <rect x="72" y="72" width="8" height="8" fill="white" />
    <rect x="84" y="80" width="8" height="8" fill="white" />
    <rect x="76" y="88" width="8" height="8" fill="white" />
    <rect x="42" y="42" width="16" height="16" rx="4" fill="#00B1C9" />
    <path d="M47 46H53M50 46V54" stroke="white" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const GeneralQR: React.FC<{ className?: string }> = ({ className = "w-24 h-24" }) => (
  <svg className={className} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="5" y="5" width="25" height="25" stroke="white" strokeWidth="4" />
    <rect x="11" y="11" width="13" height="13" fill="white" />
    <rect x="70" y="5" width="25" height="25" stroke="white" strokeWidth="4" />
    <rect x="76" y="11" width="13" height="13" fill="white" />
    <rect x="5" y="70" width="25" height="25" stroke="white" strokeWidth="4" />
    <rect x="11" y="76" width="13" height="13" fill="white" />
    <rect x="40" y="8" width="8" height="8" fill="white" />
    <rect x="52" y="15" width="8" height="8" fill="white" />
    <rect x="40" y="24" width="8" height="8" fill="white" />
    <rect x="8" y="40" width="8" height="8" fill="white" />
    <rect x="20" y="48" width="8" height="8" fill="white" />
    <rect x="12" y="56" width="8" height="8" fill="white" />
    <rect x="44" y="44" width="12" height="12" fill="white" />
    <rect x="72" y="40" width="8" height="8" fill="white" />
    <rect x="84" y="48" width="8" height="8" fill="white" />
    <rect x="76" y="56" width="8" height="8" fill="white" />
    <rect x="40" y="72" width="8" height="8" fill="white" />
    <rect x="52" y="80" width="8" height="8" fill="white" />
    <rect x="44" y="88" width="8" height="8" fill="white" />
    <rect x="72" y="72" width="8" height="8" fill="white" />
    <rect x="84" y="80" width="8" height="8" fill="white" />
    <rect x="76" y="88" width="8" height="8" fill="white" />
    <rect x="42" y="42" width="16" height="16" rx="4" fill="#0f172a" />
    <path d="M46 50H54M50 46V54" stroke="white" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const PaymentPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Selected plan metadata parsing
  const planParam = searchParams.get('plan') || 'mensual';
  const editionParam = searchParams.get('edition');

  let planName = "Plan Mensual";
  let planPrice = "S/ 14.50";
  let planPeriod = "per mes";
  let benefits = [
    "Acceso completo a todas las ediciones",
    "Historial de ediciones",
    "Lectura sin límites",
    "Desde cualquier dispositivo",
    "Soporte prioritario"
  ];
  
  if (planParam === 'diario') {
    planName = "Plan Diario";
    planPrice = "S/ 0.50";
    planPeriod = "per edición";
    benefits = [
      "Acceso a la edición del día",
      "Lectura en línea en tiempo real",
      "Desde cualquier dispositivo"
    ];
  } else if (planParam === 'semestral') {
    planName = "Plan Semestral";
    planPrice = "S/ 70.00";
    planPeriod = "per 6 meses";
  } else if (planParam === 'anual') {
    planName = "Plan Anual";
    planPrice = "S/ 120.00";
    planPeriod = "per año";
    benefits = [
      "Acceso completo a todas las ediciones",
      "Historial de ediciones",
      "Lectura sin límites",
      "Desde cualquier dispositivo",
      "Soporte prioritario",
      "Ahorra 2 meses gratis"
    ];
  } else if (editionParam) {
    planName = `Edición Digital #${editionParam}`;
    planPrice = "S/ 2.50";
    planPeriod = "pago único";
    benefits = [
      "Descarga de PDF de esta edición",
      "Lectura ilimitada en el visor",
      "Acceso de por vida"
    ];
  }

  // Flow Step: 'select_method' | 'upload_receipt'
  const [step, setStep] = useState<'select_method' | 'upload_receipt'>('select_method');
  const [paymentMethod, setPaymentMethod] = useState<'yape' | 'plin' | 'banco' | 'qr'>('yape');
  
  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  
  // UI states
  const [isCopied, setIsCopied] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [referenceNumber, setReferenceNumber] = useState('');
  const [submittedCompraId, setSubmittedCompraId] = useState<number | null>(null);

  // Copy handler
  const handleCopyNumber = (textToCopy: string) => {
    navigator.clipboard.writeText(textToCopy);
    setIsCopied(true);
    toast.success("¡Copiado al portapapeles!");
    setTimeout(() => setIsCopied(false), 2000);
  };

  // File handler
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        toast.error("Por favor, sube solo archivos de imagen (JPG, PNG).");
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        toast.error("El archivo excede el tamaño máximo permitido de 5MB.");
        return;
      }
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  // Submit handler
  const handleSubmitReceipt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      toast.error("Por favor, adjunta tu comprobante de pago.");
      return;
    }
    if (!referenceNumber.trim()) {
      toast.error("Por favor, ingresa el número de referencia.");
      return;
    }

    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('plan_code', planParam || 'mensual');
      formData.append('payment_method', paymentMethod);
      formData.append('reference_number', referenceNumber.trim());
      formData.append('receipt_image', selectedFile);

      // 1. Submit receipt screenshot to backend
      const res = await api.post('submit-receipt/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const purchaseData = res.data;
      setSubmittedCompraId(purchaseData.com_id);

      setIsSuccess(true);
      toast.success("¡Comprobante enviado correctamente!");
    } catch (err: any) {
      console.error(err);
      const detail = err.response?.data?.detail || "Error al procesar el pago.";
      toast.error(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoBack = () => {
    if (step === 'upload_receipt' && !isSuccess) {
      setStep('select_method');
    } else {
      navigate(-1);
    }
  };

  const selectPaymentMethod = (method: 'yape' | 'plin' | 'banco' | 'qr') => {
    setPaymentMethod(method);
    setStep('upload_receipt');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-800 antialiased justify-between">
      
      {/* Header matching mockup (Height adapted to step) */}
      <header className={`bg-white border-b border-slate-100 flex items-center justify-between px-6 md:px-12 shadow-sm flex-shrink-0 z-10 ${
        step === 'select_method' ? 'h-16' : 'h-14'
      }`}>
        <div className="flex items-center gap-3">
          <img src={logoAmazonia} alt="Amazonia Diario" className={step === 'select_method' ? "h-8 object-contain" : "h-7 object-contain"} />
          <div className="flex flex-col text-left">
            <span className="text-sm font-black text-[#1a4d2e] tracking-tight leading-none">Amazonia</span>
            <span className="text-[8px] font-bold text-[#ea580c] uppercase tracking-widest mt-0.5">Diario</span>
          </div>
        </div>
        
        <button 
          onClick={handleGoBack}
          className="flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-slate-900 transition-all cursor-pointer"
        >
          <ArrowLeft size={14} /> Volver a planes
        </button>
      </header>

      {/* Main Container: Dynamic Padding according to the Step */}
      <main className={`flex-1 max-w-6xl w-full mx-auto px-6 flex flex-col items-center justify-center ${
        step === 'select_method' ? 'py-12 md:py-16' : 'py-4 md:py-6'
      }`}>
        
        {isSuccess ? (
          /* SUCCESS SCREEN */
          <div className="bg-white p-8 rounded-3xl border border-slate-150 shadow-xl max-w-md w-full text-center space-y-5 animate-in zoom-in-95 duration-200">
            <div className="w-14 h-14 bg-emerald-50 border border-emerald-100 rounded-full flex items-center justify-center mx-auto text-[#1a4d2e] shadow-md">
              <CheckCircle2 size={28} className="animate-pulse" />
            </div>
            
            <div className="space-y-1">
              <h2 className="text-xl font-black text-slate-900 leading-tight">¡Comprobante enviado!</h2>
              <p className="text-xs text-slate-500 font-semibold leading-relaxed">
                Estamos validando tu pago. Una vez verificado, tu suscripción al <strong>{planName}</strong> se activará automáticamente y te enviaremos una notificación.
              </p>
            </div>

            <div className="bg-slate-50 border border-slate-100 rounded-2xl p-4 text-left space-y-3 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-bold uppercase tracking-wider text-[9px]">Suscripción</span>
                <span className="text-slate-800 font-bold">{planName}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-bold uppercase tracking-wider text-[9px]">Método</span>
                <span className="text-slate-800 font-bold uppercase">{paymentMethod}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-bold uppercase tracking-wider text-[9px]">Total pagado</span>
                <span className="text-[#ea580c] font-black">{planPrice}</span>
              </div>
            </div>

            <button
              onClick={() => navigate('/')}
              className="w-full py-3 rounded-xl text-white font-bold bg-[#1a4d2e] hover:bg-[#153e25] shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer text-xs"
            >
              Ir a mi Dashboard <Rocket size={14} />
            </button>
          </div>
        ) : (
          /* SPLIT LAYOUT IN 2 COLUMNS FOR BOTH STEPS */
          <div className={`grid grid-cols-1 lg:grid-cols-12 w-full items-stretch ${
            step === 'select_method' ? 'gap-8' : 'gap-5'
          }`}>
            
            {/* LEFT COLUMN: RESUMEN DE TU COMPRA */}
            <div className={`bg-white rounded-3xl border border-slate-200 shadow-sm flex flex-col justify-between text-left lg:col-span-4 ${
              step === 'select_method' ? 'p-6' : 'p-4'
            }`}>
              <div className={step === 'select_method' ? 'space-y-6' : 'space-y-4'}>
                <h3 className={`font-black text-slate-900 uppercase tracking-wider select-none border-b border-slate-100 pb-2.5 ${
                  step === 'select_method' ? 'text-sm' : 'text-xs'
                }`}>
                  Resumen de tu compra
                </h3>
                
                {/* Plan Selection Box */}
                <div className={`flex justify-between items-center border border-slate-100 rounded-2xl bg-slate-50/30 ${
                  step === 'select_method' ? 'p-4' : 'p-3'
                }`}>
                  <div className="flex items-center gap-3">
                    <div className={`rounded-xl bg-orange-50 border border-orange-100 flex items-center justify-center text-[#ea580c] flex-shrink-0 ${
                      step === 'select_method' ? 'w-10 h-10' : 'w-8 h-8'
                    }`}>
                      <Calendar className={step === 'select_method' ? 'w-5 h-5' : 'w-4 h-4'} />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider leading-none mb-1">Plan seleccionado</span>
                      <span className={`font-black text-slate-800 ${step === 'select_method' ? 'text-xs' : 'text-[11px]'}`}>{planName}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`font-black text-slate-800 block ${step === 'select_method' ? 'text-xs' : 'text-[11px]'}`}>{planPrice}</span>
                    <span className="text-[9px] text-slate-400 font-bold block capitalize leading-none">{planPeriod}</span>
                  </div>
                </div>

                {/* Benefits List */}
                <div className={step === 'select_method' ? 'space-y-4' : 'space-y-2.5'}>
                  <span className="text-[9px] text-slate-400 font-black uppercase tracking-wider block">Beneficios incluidos:</span>
                  <ul className={step === 'select_method' ? 'space-y-3' : 'space-y-2'}>
                    {benefits.map((benefit, i) => (
                      <li key={i} className={`flex items-start gap-2.5 text-slate-600 font-semibold leading-relaxed ${
                        step === 'select_method' ? 'text-xs' : 'text-[11px]'
                      }`}>
                        <Check className="text-[#1a4d2e] stroke-[3px] mt-0.5 flex-shrink-0" size={step === 'select_method' ? 14 : 12} />
                        <span>{benefit}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Total display box */}
              <div className={`border-t border-slate-100 ${
                step === 'select_method' ? 'pt-6 mt-8' : 'pt-4 mt-6'
              }`}>
                <div className="flex justify-between items-center">
                  <span className="text-xs font-black text-slate-500 uppercase tracking-wide">Total a pagar</span>
                  <span className={`font-black text-[#ea580c] ${
                    step === 'select_method' ? 'text-2xl' : 'text-lg'
                  }`}>{planPrice}</span>
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN: STEP 1 (CHOOSE METHOD) OR STEP 2 (INSTRUCTIONS) */}
            <div className="lg:col-span-8 flex flex-col justify-between">
              
              {step === 'select_method' ? (
                /* STEP 1: CHOOSE METHOD (Original large size as requested) */
                <div className="space-y-6 text-left animate-in fade-in duration-200">
                  <div className="space-y-1">
                    <h2 className="text-3xl font-black text-slate-900 leading-tight">Elige tu método de pago</h2>
                    <p className="text-sm text-slate-500 font-semibold leading-relaxed">
                      Selecciona la opción que más te convenga
                    </p>
                  </div>

                  <div className="space-y-4">
                    {/* Option 1: Cuenta bancaria */}
                    <button
                      type="button"
                      onClick={() => selectPaymentMethod('banco')}
                      className="w-full bg-white border border-slate-200 hover:border-slate-350 rounded-2xl p-5 flex items-center justify-between shadow-sm transition-all group active:scale-[0.99] cursor-pointer"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-center text-slate-700">
                          <Landmark size={20} />
                        </div>
                        <div>
                          <h4 className="text-sm font-black text-slate-900">Cuenta bancaria</h4>
                          <p className="text-xs text-slate-400 font-bold mt-0.5">Realiza una transferencia desde tu banca</p>
                        </div>
                      </div>
                      <ChevronRight size={18} className="text-slate-400 group-hover:text-slate-600 transition-colors" />
                    </button>

                    {/* Option 2: Yape */}
                    <button
                      type="button"
                      onClick={() => selectPaymentMethod('yape')}
                      className="w-full bg-white border border-slate-200 hover:border-slate-350 rounded-2xl p-5 flex items-center justify-between shadow-sm transition-all group active:scale-[0.99] cursor-pointer"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-purple-50 border border-purple-100 rounded-xl flex items-center justify-center">
                          <YapeLogo className="w-6 h-6" />
                        </div>
                        <div>
                          <h4 className="text-sm font-black text-slate-900">Yape</h4>
                          <p className="text-xs text-slate-400 font-bold mt-0.5">Paga de forma rápida con Yape</p>
                        </div>
                      </div>
                      <ChevronRight size={18} className="text-slate-400 group-hover:text-slate-600 transition-colors" />
                    </button>

                    {/* Option 3: Plin */}
                    <button
                      type="button"
                      onClick={() => selectPaymentMethod('plin')}
                      className="w-full bg-white border border-slate-200 hover:border-slate-350 rounded-2xl p-5 flex items-center justify-between shadow-sm transition-all group active:scale-[0.99] cursor-pointer"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-cyan-50 border border-cyan-100 rounded-xl flex items-center justify-center">
                          <PlinLogo className="w-6 h-6" />
                        </div>
                        <div>
                          <h4 className="text-sm font-black text-slate-900">Plin</h4>
                          <p className="text-xs text-slate-400 font-bold mt-0.5">Paga de forma rápida con Plin</p>
                        </div>
                      </div>
                      <ChevronRight size={18} className="text-slate-400 group-hover:text-slate-600 transition-colors" />
                    </button>

                    {/* Option 4: QR de pago */}
                    <button
                      type="button"
                      onClick={() => selectPaymentMethod('qr')}
                      className="w-full bg-white border border-slate-200 hover:border-slate-350 rounded-2xl p-5 flex items-center justify-between shadow-sm transition-all group active:scale-[0.99] cursor-pointer"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-center text-slate-700">
                          <QrCode size={20} />
                        </div>
                        <div>
                          <h4 className="text-sm font-black text-slate-900">QR de pago</h4>
                          <p className="text-xs text-slate-400 font-bold mt-0.5">Escanea y paga desde tu app bancaria</p>
                        </div>
                      </div>
                      <ChevronRight size={18} className="text-slate-400 group-hover:text-slate-600 transition-colors" />
                    </button>
                  </div>
                </div>
              ) : (
                /* STEP 2: INSTRUCTIONS & UPLOAD RECEIPT (Compact size as requested to avoid scroll) */
                <div className="space-y-4 text-left animate-in fade-in duration-200">
                  
                  {/* Payment Details Container */}
                  <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-4">
                    <h3 className="text-sm font-black text-slate-900 mb-0.5 leading-snug">
                      {paymentMethod === 'banco' ? 'Datos de Transferencia Bancaria' : `Paga con ${paymentMethod === 'qr' ? 'QR de pago' : paymentMethod === 'yape' ? 'Yape' : 'Plin'}`}
                    </h3>
                    <p className="text-[10px] text-slate-400 font-semibold mb-3">
                      {paymentMethod === 'banco' ? 'Realiza la transferencia interbancaria y adjunta el comprobante.' : 'Realiza el pago al siguiente número / QR y luego sube tu comprobante.'}
                    </p>

                    {paymentMethod === 'banco' ? (
                      /* Transfer details table */
                      <div className="space-y-2">
                        <div className="border border-slate-200 bg-slate-50/50 rounded-xl p-3 space-y-2">
                          <div className="flex justify-between items-center text-[11px] border-b border-slate-100 pb-1.5">
                            <span className="text-slate-400 font-bold uppercase tracking-wider text-[8px]">Banco</span>
                            <span className="text-slate-800 font-black">BCP (Banco de Crédito del Perú)</span>
                          </div>
                          <div className="flex justify-between items-center text-[11px] border-b border-slate-100 pb-1.5">
                            <span className="text-slate-400 font-bold uppercase tracking-wider text-[8px]">Cuenta Corriente</span>
                            <div className="flex items-center gap-1.5">
                              <span className="text-slate-800 font-black">193-4567890-0-12</span>
                              <button type="button" onClick={() => handleCopyNumber("193-4567890-0-12")} className="text-[#1a4d2e] hover:underline font-bold text-[9px]">Copiar</button>
                            </div>
                          </div>
                          <div className="flex justify-between items-center text-[11px]">
                            <span className="text-slate-400 font-bold uppercase tracking-wider text-[8px]">CCI</span>
                            <div className="flex items-center gap-1.5">
                              <span className="text-slate-800 font-black">002-19300456789001214</span>
                              <button type="button" onClick={() => handleCopyNumber("002-19300456789001214")} className="text-[#1a4d2e] hover:underline font-bold text-[9px]">Copiar</button>
                            </div>
                          </div>
                        </div>
                        <div className="text-[9px] text-slate-400 font-semibold px-1">
                          A nombre de: <strong>Amazonia Diario S.A.C.</strong>
                        </div>
                      </div>
                    ) : (
                      /* Mobile Wallet / QR display details */
                      <div className="flex flex-col sm:flex-row gap-4 items-stretch">
                        <div className="flex-1 border border-slate-200 bg-slate-50/50 rounded-xl p-3.5 flex flex-col justify-between">
                          <div>
                            <span className="text-[8px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">
                              Número de {paymentMethod === 'yape' ? 'Yape' : paymentMethod === 'plin' ? 'Plin' : 'Contacto'}
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="text-lg font-black text-slate-900 tracking-wide leading-none">987 654 321</span>
                              <button
                                type="button"
                                onClick={() => handleCopyNumber("987654321")}
                                className="inline-flex items-center gap-1 px-2 py-0.5 text-[9px] font-bold border border-slate-200 rounded bg-white hover:bg-slate-50 text-[#1a4d2e] transition-all cursor-pointer leading-none"
                              >
                                <Copy size={9} /> {isCopied ? 'Copiado' : 'Copiar'}
                              </button>
                            </div>
                          </div>

                          <div className="border-t border-slate-150 pt-2.5 mt-3">
                            <span className="text-[8px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">A nombre de</span>
                            <span className="text-[11px] font-black text-slate-800">Amazonia Diario S.A.C.</span>
                          </div>
                        </div>

                        <div className={`w-full sm:w-36 rounded-xl p-2.5 flex flex-col items-center justify-center gap-1.5 text-white text-center shadow-md ${
                          paymentMethod === 'yape' ? 'bg-[#74227E]' : paymentMethod === 'plin' ? 'bg-[#00B1C9]' : 'bg-[#0f172a]'
                        }`}>
                          <span className="text-[8px] font-black tracking-wide uppercase leading-none">Escanear el QR</span>
                          <div className="bg-white p-1 rounded-lg shadow-sm">
                            {paymentMethod === 'yape' ? <YapeQR /> : paymentMethod === 'plin' ? <PlinQR /> : <GeneralQR />}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Dropzone container */}
                  <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-4">
                    <h3 className="text-sm font-black text-slate-900 mb-0.5 leading-snug">
                      Sube tu comprobante de pago
                    </h3>
                    <p className="text-[10px] text-slate-400 font-semibold mb-3">
                      Adjunta una imagen clara de tu comprobante para validar tu suscripción.
                    </p>

                    <form onSubmit={handleSubmitReceipt} className="space-y-3.5">
                      <div className="relative border border-dashed border-slate-250 hover:border-[#1a4d2e] bg-slate-50/50 hover:bg-slate-50 rounded-xl p-4 transition-all flex flex-col items-center justify-center text-center">
                        <input
                          type="file"
                          id="receipt-upload"
                          accept="image/png, image/jpeg, image/jpg"
                          onChange={handleFileChange}
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                        />
                        
                        {previewUrl ? (
                          <div className="space-y-2 z-20">
                            <div className="w-14 h-20 mx-auto border border-slate-200 rounded overflow-hidden bg-white relative flex items-center justify-center shadow-sm">
                              <img src={previewUrl} alt="Comprobante" className="w-full h-full object-cover" />
                            </div>
                            <div className="text-[11px]">
                              <span className="font-black text-slate-800 block truncate max-w-xs">{selectedFile?.name}</span>
                              <span className="text-[9px] text-slate-400 font-bold mt-0.5">{(selectedFile!.size / (1024 * 1024)).toFixed(2)} MB</span>
                            </div>
                            <button
                              type="button"
                              onClick={() => { setSelectedFile(null); setPreviewUrl(null); }}
                              className="relative z-20 text-[9px] font-bold text-rose-600 hover:underline uppercase tracking-wide cursor-pointer"
                            >
                              Eliminar y cambiar
                            </button>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            <div className="w-9 h-9 bg-white border border-slate-200 rounded-lg flex items-center justify-center text-[#1a4d2e] shadow-sm mx-auto">
                              <Upload size={16} />
                            </div>
                            <div>
                              <p className="text-[11px] font-bold text-slate-850">
                                Arrastra tu imagen aquí o <span className="text-[#ea580c] hover:underline">haz clic para seleccionar</span>
                              </p>
                              <p className="text-[9px] text-slate-400 font-bold mt-0.5">Formatos permitidos: JPG, PNG (Máx. 5MB)</p>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Reference Number Field */}
                      <div className="space-y-1 text-left">
                        <label htmlFor="ref-number" className="text-[10px] font-black uppercase tracking-wider text-slate-500 block">
                          Número de Referencia / Operación
                        </label>
                        <input
                          type="text"
                          id="ref-number"
                          value={referenceNumber}
                          onChange={(e) => setReferenceNumber(e.target.value)}
                          placeholder="Ej. 987654321 o nro. de operación"
                          required
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-700 focus:outline-none focus:border-[#1a4d2e] focus:bg-white transition-all font-semibold"
                        />
                      </div>

                      <button
                        type="submit"
                        disabled={isSubmitting || !selectedFile || !referenceNumber.trim()}
                        className={`w-full py-2.5 rounded-xl text-white font-bold transition-all flex items-center justify-center gap-1.5 shadow-md text-xs ${
                          (!selectedFile || !referenceNumber.trim()) 
                            ? 'bg-slate-250 text-slate-400 cursor-not-allowed shadow-none' 
                            : 'bg-[#1a4d2e] hover:bg-[#153e25] shadow-brand-500/10 cursor-pointer active:scale-[0.98]'
                        }`}
                      >
                        {isSubmitting ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <>
                            <Rocket size={14} /> Enviar comprobante
                          </>
                        )}
                      </button>
                    </form>
                  </div>

                </div>
              )}

            </div>

          </div>
        )}
      </main>

      {/* Footer bar matching mockup */}
      <footer className="w-full bg-[#f8fafc] border-t border-slate-100 py-3.5 flex items-center justify-center text-[10px] text-slate-500 font-semibold gap-1.5 flex-shrink-0">
        <Lock size={11} className="text-emerald-600" />
        <span>Tu pago está 100% seguro y protegido</span>
      </footer>
    </div>
  );
};

export default PaymentPage;
