import React, { useState } from 'react';
import { useAuth } from '../contexts/auth';
import { Mail, Lock, User, Eye, EyeOff, CheckCircle2, ArrowRight, Newspaper } from 'lucide-react';
import { toast } from 'sonner';

export function AuthForm() {
  const {
    login,
    register,
    resendVerification
  } = useAuth();

  const [isLoginTab, setIsLoginTab] = useState(true);
  
  // States para Login
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  // States para Registro
  const [regNombres, setRegNombres] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');
  const [showRegPassword, setShowRegPassword] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [isRegisteredSuccess, setIsRegisteredSuccess] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState('');

  // States generales
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginEmail || !loginPassword) {
      toast.error('Por favor, completa todos los campos.');
      return;
    }
    
    setIsSubmitting(true);
    const result = await login(loginEmail, loginPassword);
    setIsSubmitting(false);

    if (result.success) {
      toast.success('¡Sesión iniciada correctamente!');
      setLoginEmail('');
      setLoginPassword('');
    } else {
      toast.error(result.error || 'Error al iniciar sesión.');
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regNombres || !regEmail || !regPassword || !regConfirmPassword) {
      toast.error('Por favor, completa todos los campos obligatorios.');
      return;
    }

    if (regPassword !== regConfirmPassword) {
      toast.error('Las contraseñas no coinciden.');
      return;
    }

    if (regPassword.length < 8) {
      toast.error('La contraseña debe tener al menos 8 caracteres.');
      return;
    }

    if (!acceptTerms) {
      toast.error('Debes aceptar los términos y condiciones.');
      return;
    }

    setIsSubmitting(true);
    const result = await register(regNombres, regEmail, regPassword);
    setIsSubmitting(false);

    if (result.success) {
      toast.success('¡Usuario registrado con éxito!');
      setRegisteredEmail(regEmail);
      setIsRegisteredSuccess(true);
      // Reset form
      setRegNombres('');
      setRegEmail('');
      setRegPassword('');
      setRegConfirmPassword('');
      setAcceptTerms(false);
    } else {
      toast.error(result.error || 'Error durante el registro.');
    }
  };

  const handleResendClick = async () => {
    if (!registeredEmail) return;
    setIsSubmitting(true);
    const result = await resendVerification(registeredEmail);
    setIsSubmitting(false);

    if (result.success) {
      toast.success(result.message || 'Código de verificación reenviado a tu correo.');
    } else {
      toast.error(result.error || 'Error al reenviar el correo.');
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1f13] bg-gradient-to-br from-[#0b1f13] via-[#113a20] to-[#07130b] flex flex-col items-center justify-center p-4 relative overflow-hidden text-left">
      
      {/* Background decoration blur bubbles */}
      <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-[#ea580c]/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-[#1a4d2e]/40 rounded-full blur-[120px] pointer-events-none" />

      {/* Brand logo top */}
      <div className="flex items-center gap-3.5 mb-8 relative z-10">
        <div className="w-11 h-11 bg-brand-600 rounded-2xl flex items-center justify-center shadow-lg shadow-brand-500/25 border border-brand-400/20">
          <Newspaper className="w-5 h-5 text-white" />
        </div>
        <div className="flex flex-col">
          <span className="text-xl font-black text-white tracking-tight leading-none">Amazonia</span>
          <span className="text-[10px] font-bold text-brand-400 uppercase tracking-widest mt-1">Periódico Digital</span>
        </div>
      </div>

      {/* Auth Card */}
      <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-emerald-50 overflow-hidden z-10 transform transition-all duration-300 scale-100 flex flex-col max-h-[90vh] overflow-y-auto">
        {/* Top brand header bar */}
        <div className="h-2 w-full bg-gradient-to-r from-[#1a4d2e] via-[#ea580c] to-[#1a4d2e]" />

        {/* Content Area */}
        <div className="p-8">
          {isRegisteredSuccess ? (
            /* Pantalla de éxito en registro (Verificación pendiente) */
            <div className="text-center py-6 flex flex-col items-center">
              <div className="w-16 h-16 bg-emerald-50 border border-emerald-100 rounded-full flex items-center justify-center mb-6 animate-bounce">
                <CheckCircle2 size={32} className="text-[#1a4d2e]" />
              </div>
              <h3 className="text-2xl font-black text-slate-800 mb-3">¡Casi listo!</h3>
              <p className="text-sm text-slate-600 mb-6 leading-relaxed">
                Hemos enviado un enlace de activación a <strong className="text-slate-800">{registeredEmail}</strong>. 
                Por favor, revisa tu correo y haz clic en el enlace para activar tu cuenta.
              </p>
              
              <div className="w-full bg-[#f8fafc] border border-slate-100 rounded-2xl p-4 mb-6">
                <p className="text-[11px] text-gray-500 font-medium leading-normal">
                  ¿No recibiste el correo? Revisa tu carpeta de spam o solicita un nuevo reenvío abajo.
                </p>
              </div>

              <div className="flex flex-col gap-3 w-full">
                <button
                  onClick={handleResendClick}
                  disabled={isSubmitting}
                  className="w-full py-3 px-4 rounded-xl text-white font-bold bg-[#ea580c] hover:bg-[#d44f0a] transition-all flex items-center justify-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    'Reenviar enlace de activación'
                  )}
                </button>
                <button
                  onClick={() => {
                    setIsRegisteredSuccess(false);
                    setIsLoginTab(true);
                  }}
                  className="w-full py-3 px-4 rounded-xl text-[#1a4d2e] font-bold border border-slate-200 hover:bg-slate-50 transition-colors flex items-center justify-center gap-2"
                >
                  Volver al inicio de sesión
                </button>
              </div>
            </div>
          ) : (
            /* Formularios de Login / Registro */
            <>
              {/* Header Tabs */}
              <div className="flex bg-[#f1f5f9] p-1 rounded-2xl mb-8">
                <button
                  onClick={() => setIsLoginTab(true)}
                  className={`flex-1 py-2.5 text-xs font-black rounded-xl transition-all ${
                    isLoginTab 
                      ? 'bg-white text-[#1a4d2e] shadow-sm' 
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  INICIAR SESIÓN
                </button>
                <button
                  onClick={() => setIsLoginTab(false)}
                  className={`flex-1 py-2.5 text-xs font-black rounded-xl transition-all ${
                    !isLoginTab 
                      ? 'bg-white text-[#1a4d2e] shadow-sm' 
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  REGISTRARSE
                </button>
              </div>

              {/* Título de la pestaña */}
              <div className="mb-6">
                <h3 className="text-2xl font-black text-slate-800">
                  {isLoginTab ? '¡Hola de nuevo!' : 'Crea tu cuenta'}
                </h3>
                <p className="text-xs text-slate-500 mt-1 font-medium">
                  {isLoginTab 
                    ? 'Accede a tus suscripciones y ediciones digitales.' 
                    : 'Regístrate hoy y accede a contenido exclusivo de Amazonia.'}
                </p>
              </div>

              {isLoginTab ? (
                /* FORMULARIO LOGIN */
                <form onSubmit={handleLoginSubmit} className="space-y-4">
                  {/* Email */}
                  <div>
                    <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider mb-1.5">
                      Correo Electrónico
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                        <Mail size={18} />
                      </div>
                      <input
                        type="text"
                        required
                        placeholder="tu@correo.com"
                        value={loginEmail}
                        onChange={(e) => setLoginEmail(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all"
                      />
                    </div>
                  </div>

                  {/* Contraseña */}
                  <div>
                    <div className="flex justify-between items-center mb-1.5">
                      <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider">
                        Contraseña
                      </label>
                      <a href="#" className="text-[11px] font-bold text-[#ea580c] hover:underline">
                        ¿La olvidaste?
                      </a>
                    </div>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                        <Lock size={18} />
                      </div>
                      <input
                        type={showLoginPassword ? 'text' : 'password'}
                        required
                        placeholder="••••••••"
                        value={loginPassword}
                        onChange={(e) => setLoginPassword(e.target.value)}
                        className="w-full pl-10 pr-10 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all"
                      />
                      <button
                        type="button"
                        onClick={() => setShowLoginPassword(!showLoginPassword)}
                        className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600"
                      >
                        {showLoginPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full py-3.5 px-4 rounded-xl text-white font-bold bg-[#1a4d2e] hover:bg-[#153e25] transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg active:scale-[0.98] duration-150 disabled:opacity-50 disabled:cursor-not-allowed mt-6"
                  >
                    {isSubmitting ? (
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        Iniciar sesión
                        <ArrowRight size={18} />
                      </>
                    )}
                  </button>
                </form>
              ) : (
                /* FORMULARIO REGISTRO */
                <form onSubmit={handleRegisterSubmit} className="space-y-4">
                  {/* Nombres */}
                  <div>
                    <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider mb-1.5">
                      Nombres Completos
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                        <User size={18} />
                      </div>
                      <input
                        type="text"
                        required
                        placeholder="Juan Pérez"
                        value={regNombres}
                        onChange={(e) => setRegNombres(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all"
                      />
                    </div>
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider mb-1.5">
                      Correo Electrónico
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                        <Mail size={18} />
                      </div>
                      <input
                        type="email"
                        required
                        placeholder="tu@correo.com"
                        value={regEmail}
                        onChange={(e) => setRegEmail(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all"
                      />
                    </div>
                  </div>

                  {/* Contraseña */}
                  <div>
                    <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider mb-1.5">
                      Contraseña (mínimo 8 caracteres)
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                        <Lock size={18} />
                      </div>
                      <input
                        type={showRegPassword ? 'text' : 'password'}
                        required
                        placeholder="••••••••"
                        value={regPassword}
                        onChange={(e) => setRegPassword(e.target.value)}
                        className="w-full pl-10 pr-10 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all"
                      />
                      <button
                        type="button"
                        onClick={() => setShowRegPassword(!showRegPassword)}
                        className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600"
                      >
                        {showRegPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  {/* Confirmar Contraseña */}
                  <div>
                    <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider mb-1.5">
                      Confirmar Contraseña
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                        <Lock size={18} />
                      </div>
                      <input
                        type="password"
                        required
                        placeholder="••••••••"
                        value={regConfirmPassword}
                        onChange={(e) => setRegConfirmPassword(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all"
                      />
                    </div>
                  </div>

                  {/* Términos y condiciones */}
                  <div className="flex items-start gap-2.5 mt-2">
                    <input
                      type="checkbox"
                      id="terms"
                      checked={acceptTerms}
                      onChange={(e) => setAcceptTerms(e.target.checked)}
                      className="mt-0.5 w-4 h-4 rounded text-[#1a4d2e] focus:ring-[#1a4d2e] border-slate-300"
                    />
                    <label htmlFor="terms" className="text-[11px] text-slate-500 font-medium leading-tight select-none">
                      Acepto los <a href="#" className="text-[#ea580c] font-semibold hover:underline">términos de servicio</a> y la <a href="#" className="text-[#ea580c] font-semibold hover:underline">política de privacidad</a> de Amazonia.
                    </label>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full py-3.5 px-4 rounded-xl text-white font-bold bg-[#ea580c] hover:bg-[#d44f0a] transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg active:scale-[0.98] duration-150 disabled:opacity-50 disabled:cursor-not-allowed mt-6"
                  >
                    {isSubmitting ? (
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        Crear mi cuenta
                        <ArrowRight size={18} />
                      </>
                    )}
                  </button>
                </form>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
