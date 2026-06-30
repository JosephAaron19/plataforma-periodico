import React, { useState } from 'react';
import { useAuth } from '../contexts/auth';
import { X, Mail, Lock, User, Eye, EyeOff, CheckCircle2, ArrowRight, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

export function AuthModal() {
  const {
    showAuthModal,
    authModalTab,
    closeAuthModal,
    openAuthModal,
    login,
    register,
    resendVerification,
    requestPasswordReset,
    confirmPasswordReset
  } = useAuth();

  const [authView, setAuthView] = useState<'login' | 'register' | 'forgot' | 'reset'>('login');
  
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

  // States para Olvido de Contraseña
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotError, setForgotError] = useState('');
  const [forgotSuccess, setForgotSuccess] = useState('');

  // States para Restablecimiento de Contraseña
  const [resetToken, setResetToken] = useState('');
  const [resetPassword, setResetPassword] = useState('');
  const [resetConfirmPassword, setResetConfirmPassword] = useState('');
  const [showResetPassword, setShowResetPassword] = useState(false);
  const [resetError, setResetError] = useState('');
  const [resetSuccess, setResetSuccess] = useState('');

  // States generales
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Sincronizar vista interna con la del contexto al abrirse
  React.useEffect(() => {
    if (showAuthModal) {
      if (resetToken) {
        setAuthView('reset');
      } else {
        setAuthView(authModalTab === 'register' ? 'register' : 'login');
      }
      setIsRegisteredSuccess(false);
      setForgotError('');
      setForgotSuccess('');
      setResetError('');
      setResetSuccess('');
    }
  }, [authModalTab, showAuthModal, resetToken]);

  // Detectar token de restablecimiento en la URL
  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('reset-token');
    if (token) {
      setResetToken(token);
      setAuthView('reset');
      openAuthModal('login'); // Abre el modal
      // Limpiar query params de la URL sin recargar la página
      const cleanUrl = window.location.origin + window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    }
  }, []);

  if (!showAuthModal) return null;

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

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotError('');
    setForgotSuccess('');

    if (!forgotEmail) {
      setForgotError('El correo electrónico es obligatorio');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(forgotEmail)) {
      setForgotError('Ingresa un correo electrónico válido');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await requestPasswordReset(forgotEmail);
      setIsSubmitting(false);

      if (result.success) {
        setForgotSuccess(result.message || 'Se ha enviado un correo con instrucciones para restablecer tu contraseña.');
        setForgotEmail('');
      } else {
        setForgotError(result.error || 'El correo ingresado no se encuentra registrado.');
      }
    } catch (err) {
      setIsSubmitting(false);
      setForgotError('Ocurrió un error de red al intentar enviar el correo. Por favor, verifica tu conexión.');
    }
  };

  const handleResetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setResetError('');
    setResetSuccess('');

    if (!resetPassword || !resetConfirmPassword) {
      setResetError('Por favor completa todos los campos.');
      return;
    }

    if (resetPassword !== resetConfirmPassword) {
      setResetError('Las contraseñas no coinciden.');
      return;
    }

    if (resetPassword.length < 8) {
      setResetError('La contraseña debe tener al menos 8 caracteres.');
      return;
    }

    const hasNumber = /\d/.test(resetPassword);
    const hasUpper = /[A-Z]/.test(resetPassword);
    const hasSymbol = /[^a-zA-Z0-9]/.test(resetPassword);

    if (!hasNumber || !hasUpper || !hasSymbol) {
      setResetError('La contraseña debe cumplir con los requisitos mínimos (mínimo 8 caracteres, al menos un número, una letra mayúscula y un símbolo).');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await confirmPasswordReset(resetToken, resetPassword);
      setIsSubmitting(false);

      if (result.success) {
        toast.success(result.message || 'Contraseña actualizada correctamente. Ahora puedes iniciar sesión.');
        setResetSuccess('Contraseña actualizada correctamente. Ahora puedes iniciar sesión.');
        
        setTimeout(() => {
          setResetPassword('');
          setResetConfirmPassword('');
          setResetToken('');
          setResetSuccess('');
          setAuthView('login');
          closeAuthModal(); // Cierre automático al completar correctamente
        }, 2000);
      } else {
        setResetError(result.error || 'Error al restablecer la contraseña.');
      }
    } catch (err) {
      setIsSubmitting(false);
      setResetError('Ocurrió un error de red al restablecer la contraseña. Por favor, verifica tu conexión.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay con blur y transición */}
      <div 
        className="fixed inset-0 bg-[#0b1f13]/60 backdrop-blur-md transition-opacity duration-300"
        onClick={closeAuthModal}
      />

      {/* Modal Card */}
      <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-emerald-50 overflow-hidden z-10 transform transition-all duration-300 scale-100 flex flex-col max-h-[90vh] overflow-y-auto">
        {/* Top brand header bar */}
        <div className="h-2 w-full bg-gradient-to-r from-[#1a4d2e] via-[#ea580c] to-[#1a4d2e]" />
        
        {/* Close Button */}
        <button 
          onClick={closeAuthModal}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition-colors p-1.5 rounded-full hover:bg-slate-100"
        >
          <X size={20} />
        </button>

        {/* Content Area */}
        <div className="p-8 text-slate-800">
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
                  className="w-full py-3 px-4 rounded-xl text-white font-bold bg-[#ea580c] hover:bg-[#d44f0a] transition-all flex items-center justify-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
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
                    setAuthView('login');
                  }}
                  className="w-full py-3 px-4 rounded-xl text-[#1a4d2e] font-bold border border-slate-200 hover:bg-slate-50 transition-colors flex items-center justify-center gap-2 cursor-pointer"
                >
                  Volver al inicio de sesión
                </button>
              </div>
            </div>
          ) : authView === 'forgot' ? (
            /* FORMULARIO RECUPERACIÓN */
            <div className="space-y-6">
              <div>
                <h3 className="text-2xl font-black text-slate-800 text-left">Recuperar contraseña</h3>
                <p className="text-xs text-slate-500 mt-1 font-medium text-left">
                  Ingresa tu correo electrónico registrado y te enviaremos un enlace para restablecer tu contraseña.
                </p>
              </div>

              {/* Alertas Inline */}
              {forgotError && (
                <div className="p-4 bg-red-50 border border-red-100 rounded-2xl flex items-start gap-3 text-left animate-in fade-in duration-200">
                  <AlertCircle size={18} className="text-red-600 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-red-700 font-semibold leading-relaxed">{forgotError}</p>
                </div>
              )}

              {forgotSuccess && (
                <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-2xl flex items-start gap-3 text-left animate-in fade-in duration-200">
                  <CheckCircle2 size={18} className="text-[#1a4d2e] flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-emerald-800 font-semibold leading-relaxed">{forgotSuccess}</p>
                </div>
              )}

              <form onSubmit={handleForgotSubmit} className="space-y-4">
                <div>
                  <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider mb-1.5 text-left">
                    Correo Electrónico
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Mail size={18} />
                    </div>
                    <input
                      type="text"
                      placeholder="tu@correo.com"
                      value={forgotEmail}
                      onChange={(e) => setForgotEmail(e.target.value)}
                      className="w-full pl-10 pr-4 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all text-slate-800"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting || !!forgotSuccess}
                  className="w-full py-3.5 px-4 rounded-xl text-white font-bold bg-[#1a4d2e] hover:bg-[#153e25] transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg active:scale-[0.98] duration-150 disabled:opacity-50 disabled:cursor-not-allowed mt-6 cursor-pointer"
                >
                  {isSubmitting ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      Enviar correo de recuperación
                      <ArrowRight size={18} />
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => setAuthView('login')}
                  className="w-full py-3 px-4 rounded-xl text-slate-500 font-bold border border-slate-200 hover:bg-slate-50 transition-colors flex items-center justify-center gap-2 mt-2 cursor-pointer text-xs"
                >
                  Volver al inicio de sesión
                </button>
              </form>
            </div>
          ) : authView === 'reset' ? (
            /* FORMULARIO RESTABLECIMIENTO */
            <div className="space-y-6">
              <div>
                <h3 className="text-2xl font-black text-slate-800 text-left">Restablecer contraseña</h3>
                <p className="text-xs text-slate-500 mt-1 font-medium text-left">
                  Crea una nueva contraseña segura para tu cuenta.
                </p>
              </div>

              {/* Alertas Inline */}
              {resetError && (
                <div className="p-4 bg-red-50 border border-red-100 rounded-2xl flex items-start gap-3 text-left animate-in fade-in duration-200">
                  <AlertCircle size={18} className="text-red-600 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-red-700 font-semibold leading-relaxed">{resetError}</p>
                </div>
              )}

              {resetSuccess && (
                <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-2xl flex items-start gap-3 text-left animate-in fade-in duration-200">
                  <CheckCircle2 size={18} className="text-[#1a4d2e] flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-emerald-800 font-semibold leading-relaxed">{resetSuccess}</p>
                </div>
              )}

              {/* Requisitos mínimos de contraseña */}
              <div className="p-4 bg-[#f8fafc] border border-slate-100 rounded-2xl text-left">
                <h4 className="text-[10px] font-black text-slate-700 uppercase tracking-wider mb-2">Requisitos de contraseña:</h4>
                <ul className="space-y-1.5">
                  {[
                    { label: 'Mínimo 8 caracteres', checked: resetPassword.length >= 8 },
                    { label: 'Al menos un número', checked: /\d/.test(resetPassword) },
                    { label: 'Al menos una letra mayúscula', checked: /[A-Z]/.test(resetPassword) },
                    { label: 'Al menos un símbolo especial', checked: /[^a-zA-Z0-9]/.test(resetPassword) },
                  ].map((req, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-xs font-semibold">
                      <span className={`w-1.5 h-1.5 rounded-full ${req.checked ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                      <span className={req.checked ? 'text-emerald-700 font-bold' : 'text-slate-500'}>{req.label}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <form onSubmit={handleResetSubmit} className="space-y-4">
                {/* Nueva Contraseña */}
                <div>
                  <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider mb-1.5 text-left">
                    Nueva Contraseña
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Lock size={18} />
                    </div>
                    <input
                      type={showResetPassword ? 'text' : 'password'}
                      required
                      placeholder="••••••••"
                      value={resetPassword}
                      onChange={(e) => setResetPassword(e.target.value)}
                      className="w-full pl-10 pr-10 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all text-slate-800"
                    />
                    <button
                      type="button"
                      onClick={() => setShowResetPassword(!showResetPassword)}
                      className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 cursor-pointer"
                    >
                      {showResetPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                {/* Confirmar Contraseña */}
                <div>
                  <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider mb-1.5 text-left">
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
                      value={resetConfirmPassword}
                      onChange={(e) => setResetConfirmPassword(e.target.value)}
                      className="w-full pl-10 pr-4 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all text-slate-800"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting || !!resetSuccess}
                  className="w-full py-3.5 px-4 rounded-xl text-white font-bold bg-[#ea580c] hover:bg-[#d44f0a] transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg active:scale-[0.98] duration-150 disabled:opacity-50 disabled:cursor-not-allowed mt-6 cursor-pointer"
                >
                  {isSubmitting ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      Restablecer contraseña
                      <ArrowRight size={18} />
                    </>
                  )}
                </button>
              </form>
            </div>
          ) : (
            /* Formularios de Login / Registro */
            <>
              {/* Header Tabs */}
              <div className="flex bg-[#f1f5f9] p-1 rounded-2xl mb-8">
                <button
                  onClick={() => setAuthView('login')}
                  className={`flex-1 py-2.5 text-xs font-black rounded-xl transition-all cursor-pointer ${
                    authView === 'login' 
                      ? 'bg-white text-[#1a4d2e] shadow-sm' 
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  INICIAR SESIÓN
                </button>
                <button
                  onClick={() => setAuthView('register')}
                  className={`flex-1 py-2.5 text-xs font-black rounded-xl transition-all cursor-pointer ${
                    authView === 'register' 
                      ? 'bg-white text-[#1a4d2e] shadow-sm' 
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  REGISTRARSE
                </button>
              </div>

              {/* Título de la pestaña */}
              <div className="mb-6">
                <h3 className="text-2xl font-black text-slate-800 text-left">
                  {authView === 'login' ? '¡Hola de nuevo!' : 'Crea tu cuenta'}
                </h3>
                <p className="text-xs text-slate-500 mt-1 font-medium text-left">
                  {authView === 'login' 
                    ? 'Accede a tus suscripciones y ediciones digitales.' 
                    : 'Regístrate hoy y accede a contenido exclusivo de Amazonia.'}
                </p>
              </div>

              {authView === 'login' ? (
                /* FORMULARIO LOGIN */
                <form onSubmit={handleLoginSubmit} className="space-y-4">
                  {/* Email */}
                  <div>
                    <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider mb-1.5 text-left">
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
                        className="w-full pl-10 pr-4 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all text-slate-800"
                      />
                    </div>
                  </div>

                  {/* Contraseña */}
                  <div>
                    <div className="flex justify-between items-center mb-1.5">
                      <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider">
                        Contraseña
                      </label>
                      <button
                        type="button"
                        onClick={() => setAuthView('forgot')}
                        className="text-[11px] font-bold text-[#ea580c] hover:underline bg-transparent border-0 cursor-pointer focus:outline-none"
                      >
                        ¿La olvidaste?
                      </button>
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
                        className="w-full pl-10 pr-10 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all text-slate-800"
                      />
                      <button
                        type="button"
                        onClick={() => setShowLoginPassword(!showLoginPassword)}
                        className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 cursor-pointer"
                      >
                        {showLoginPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full py-3.5 px-4 rounded-xl text-white font-bold bg-[#1a4d2e] hover:bg-[#153e25] transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg active:scale-[0.98] duration-150 disabled:opacity-50 disabled:cursor-not-allowed mt-6 cursor-pointer"
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
                    <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider mb-1.5 text-left">
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
                        className="w-full pl-10 pr-4 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all text-slate-800"
                      />
                    </div>
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider mb-1.5 text-left">
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
                        className="w-full pl-10 pr-4 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all text-slate-800"
                      />
                    </div>
                  </div>

                  {/* Contraseña */}
                  <div>
                    <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider mb-1.5 text-left">
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
                        className="w-full pl-10 pr-10 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all text-slate-800"
                      />
                      <button
                        type="button"
                        onClick={() => setShowRegPassword(!showRegPassword)}
                        className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 cursor-pointer"
                      >
                        {showRegPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  {/* Confirmar Contraseña */}
                  <div>
                    <label className="block text-[11px] font-black text-slate-700 uppercase tracking-wider mb-1.5 text-left">
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
                        className="w-full pl-10 pr-4 py-3 bg-[#f8fafc] border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#1a4d2e]/20 focus:border-[#1a4d2e] transition-all text-slate-800"
                      />
                    </div>
                  </div>

                  {/* Términos y condiciones */}
                  <div className="flex items-start gap-2.5 mt-2 text-left">
                    <input
                      type="checkbox"
                      id="terms"
                      checked={acceptTerms}
                      onChange={(e) => setAcceptTerms(e.target.checked)}
                      className="mt-0.5 w-4 h-4 rounded text-[#1a4d2e] focus:ring-[#1a4d2e] border-slate-300 cursor-pointer"
                    />
                    <label htmlFor="terms" className="text-[11px] text-slate-500 font-medium leading-tight select-none">
                      Acepto los <a href="#" className="text-[#ea580c] font-semibold hover:underline">términos de servicio</a> y la <a href="#" className="text-[#ea580c] font-semibold hover:underline">política de privacidad</a> de Amazonia.
                    </label>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full py-3.5 px-4 rounded-xl text-white font-bold bg-[#ea580c] hover:bg-[#d44f0a] transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg active:scale-[0.98] duration-150 disabled:opacity-50 disabled:cursor-not-allowed mt-6 cursor-pointer"
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
