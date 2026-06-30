import React, { useEffect, useState, useRef } from 'react';
import { useAuth } from '../contexts/auth';
import { CheckCircle2, XCircle, Loader2, Mail, ArrowRight, Home } from 'lucide-react';
import confetti from 'canvas-confetti';
import { toast } from 'sonner';

export function VerifyEmailPage() {
  const { verifyEmail, resendVerification, openAuthModal } = useAuth();
  
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState('');
  
  // Reenvío de correo
  const [email, setEmail] = useState('');
  const [isResending, setIsResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  // Evitar doble ejecución en React StrictMode
  const verificationStarted = useRef(false);

  useEffect(() => {
    if (verificationStarted.current) return;
    verificationStarted.current = true;

    const queryParams = new URLSearchParams(window.location.search);
    const token = queryParams.get('token');

    if (!token) {
      setStatus('error');
      setErrorMessage('No se encontró ningún token de verificación en la dirección URL.');
      return;
    }

    const runVerification = async () => {
      setStatus('loading');
      // Esperar un breve momento para dar una transición suave
      await new Promise((resolve) => setTimeout(resolve, 1500));
      
      const result = await verifyEmail(token);
      
      if (result.success) {
        setStatus('success');
        // Lanzar confeti premium
        triggerConfetti();
        toast.success('¡Cuenta activada con éxito!');
      } else {
        setStatus('error');
        setErrorMessage(result.error || 'El enlace de verificación es inválido o ha expirado.');
      }
    };

    runVerification();
  }, []);

  const triggerConfetti = () => {
    // Configuración de confeti elegante y celebradora
    const duration = 3 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

    const randomInRange = (min: number, max: number) => {
      return Math.random() * (max - min) + min;
    };

    const interval: any = setInterval(function() {
      const timeLeft = animationEnd - Date.now();

      if (timeLeft <= 0) {
        return clearInterval(interval);
      }

      const particleCount = 50 * (timeLeft / duration);
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } });
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } });
    }, 250);
  };

  const handleResendSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      toast.error('Por favor, ingresa tu correo electrónico.');
      return;
    }

    setIsResending(true);
    const result = await resendVerification(email);
    setIsResending(false);

    if (result.success) {
      setResendSuccess(true);
      toast.success(result.message || 'Enlace de verificación reenviado.');
    } else {
      toast.error(result.error || 'Error al reenviar la verificación.');
    }
  };

  const handleGoHome = () => {
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Círculos decorativos con gradientes de marca */}
      <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] rounded-full bg-emerald-500/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] rounded-full bg-orange-500/5 blur-[120px] pointer-events-none" />

      {/* Tarjeta de verificación */}
      <div className="w-full max-w-md bg-white rounded-3xl shadow-xl border border-emerald-50/50 overflow-hidden relative z-10 transform transition-all duration-500 hover:shadow-2xl">
        <div className="h-2 w-full bg-gradient-to-r from-[#1a4d2e] via-[#ea580c] to-[#1a4d2e]" />
        
        <div className="p-8 md:p-10 text-center">
          
          {status === 'loading' && (
            <div className="py-12 flex flex-col items-center">
              <div className="relative mb-6">
                <div className="w-20 h-20 rounded-full border-4 border-emerald-50 border-t-[#1a4d2e] animate-spin" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Loader2 size={32} className="text-[#1a4d2e] animate-pulse" />
                </div>
              </div>
              <h3 className="text-xl font-black text-slate-800 mb-2">Verificando tu cuenta</h3>
              <p className="text-sm text-slate-500 max-w-xs leading-relaxed font-medium">
                Por favor, espera un momento mientras validamos tus datos de activación...
              </p>
            </div>
          )}

          {status === 'success' && (
            <div className="py-6 flex flex-col items-center animate-fade-in">
              <div className="w-20 h-20 bg-emerald-50 border border-emerald-100 rounded-full flex items-center justify-center mb-6 text-[#1a4d2e] shadow-inner">
                <CheckCircle2 size={40} className="animate-scale-up" />
              </div>
              
              <h3 className="text-2xl font-black text-[#1a4d2e] mb-3">¡Correo verificado!</h3>
              <p className="text-sm text-slate-600 mb-8 leading-relaxed max-w-sm font-medium">
                Tu cuenta ha sido activada con éxito. Ya puedes disfrutar de todas nuestras ediciones digitales y contenido exclusivo.
              </p>

              <div className="flex flex-col gap-3 w-full">
                <button
                  onClick={() => {
                    // Redirigir a la raíz y abrir el login modal
                    window.history.replaceState({}, document.title, window.location.pathname);
                    openAuthModal('login');
                  }}
                  className="w-full py-4 px-6 rounded-xl text-white font-bold bg-[#1a4d2e] hover:bg-[#153e25] transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg active:scale-[0.98] duration-150"
                >
                  Iniciar sesión ahora
                  <ArrowRight size={18} />
                </button>
                
                <button
                  onClick={handleGoHome}
                  className="w-full py-3 px-6 rounded-xl text-slate-600 font-bold hover:bg-slate-50 transition-colors flex items-center justify-center gap-2"
                >
                  <Home size={18} />
                  Ir al inicio
                </button>
              </div>
            </div>
          )}

          {status === 'error' && (
            <div className="py-6 flex flex-col items-center">
              <div className="w-20 h-20 bg-orange-50 border border-orange-100 rounded-full flex items-center justify-center mb-6 text-[#ea580c]">
                <XCircle size={40} />
              </div>

              <h3 className="text-2xl font-black text-slate-800 mb-3">Verificación fallida</h3>
              <p className="text-sm text-slate-500 mb-8 leading-relaxed font-medium">
                {errorMessage}
              </p>

              {resendSuccess ? (
                <div className="w-full bg-emerald-50 border border-emerald-100 rounded-2xl p-5 text-left mb-6">
                  <h4 className="text-xs font-black text-[#1a4d2e] mb-1.5 uppercase tracking-wider">¡Correo enviado!</h4>
                  <p className="text-xs text-emerald-800 leading-relaxed font-medium">
                    Hemos enviado un nuevo enlace de activación. Por favor, revisa tu correo electrónico (también la carpeta de spam).
                  </p>
                </div>
              ) : (
                <div className="w-full bg-[#f8fafc] border border-slate-100 rounded-2xl p-6 text-left mb-8">
                  <h4 className="text-xs font-black text-slate-800 mb-2 uppercase tracking-wider">
                    ¿Quieres recibir un nuevo enlace?
                  </h4>
                  <p className="text-xs text-slate-500 mb-4 leading-relaxed font-medium">
                    Ingresa tu correo abajo y te enviaremos un nuevo enlace de activación inmediatamente.
                  </p>
                  
                  <form onSubmit={handleResendSubmit} className="space-y-3">
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                        <Mail size={16} />
                      </div>
                      <input
                        type="email"
                        required
                        placeholder="tu@correo.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full pl-9 pr-3 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-medium focus:outline-none focus:ring-2 focus:ring-[#ea580c]/20 focus:border-[#ea580c] transition-all"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={isResending}
                      className="w-full py-2.5 px-4 rounded-xl text-white text-xs font-bold bg-[#ea580c] hover:bg-[#d44f0a] transition-all flex items-center justify-center gap-1.5 shadow-sm disabled:opacity-50"
                    >
                      {isResending ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        'Solicitar nuevo enlace'
                      )}
                    </button>
                  </form>
                </div>
              )}

              <button
                onClick={handleGoHome}
                className="w-full py-3 px-6 rounded-xl text-slate-600 font-bold border border-slate-200 hover:bg-slate-50 transition-colors flex items-center justify-center gap-2"
              >
                <Home size={18} />
                Volver al inicio
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
