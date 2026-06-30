import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { BookOpen, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import api from '../../services/api';

const VerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const performVerification = async () => {
      if (!token) {
        setStatus('error');
        setMessage('Falta el token de verificación en el enlace. Por favor, solicita un nuevo correo de activación.');
        return;
      }

      try {
        const response = await api.post('/auth/verify-email/', { token });
        setStatus('success');
        setMessage(response.data.message || '¡Tu correo electrónico ha sido verificado con éxito! Ya puedes iniciar sesión.');
      } catch (err: any) {
        setStatus('error');
        let errorMsg = 'El token no es válido o ha expirado. Por favor, solicita un nuevo enlace de activación.';
        if (err.response?.data) {
          const data = err.response.data;
          if (typeof data === 'object') {
            if (data.error) {
              errorMsg = data.error;
            } else if (data.detail) {
              errorMsg = data.detail;
            } else {
              errorMsg = Object.entries(data)
                .map(([key, val]) => {
                  const valStr = Array.isArray(val) ? val.join(' ') : String(val);
                  const keyName = key === 'token' ? 'Token' : key;
                  return `${keyName}: ${valStr}`;
                })
                .join(' | ');
            }
          } else if (typeof data === 'string') {
            errorMsg = data;
          }
        }
        setMessage(errorMsg);
      }
    };

    performVerification();
  }, [token]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center items-center gap-2 mb-6">
          <BookOpen className="h-10 w-10 text-brand-600" />
          <span className="text-2xl font-bold text-gray-900">DigitalSaaS</span>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Verificación de Cuenta
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-2xl sm:px-10 border border-gray-100 text-center">
          
          {status === 'loading' && (
            <div className="flex flex-col items-center py-6">
              <Loader className="h-12 w-12 text-brand-600 animate-spin mb-4" />
              <p className="text-gray-600 font-medium">Verificando tu cuenta, por favor espera...</p>
            </div>
          )}

          {status === 'success' && (
            <div className="flex flex-col items-center py-6">
              <CheckCircle className="h-16 w-16 text-green-500 mb-4" />
              <p className="text-gray-900 font-semibold text-lg mb-2">¡Activación Exitosa!</p>
              <p className="text-gray-600 text-sm mb-6 max-w-sm">
                {message}
              </p>
              <Link
                to="/login"
                state={{ message }}
                className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 transition-colors"
              >
                Iniciar Sesión
              </Link>
            </div>
          )}

          {status === 'error' && (
            <div className="flex flex-col items-center py-6">
              <AlertCircle className="h-16 w-16 text-red-500 mb-4" />
              <p className="text-gray-900 font-semibold text-lg mb-2">No se pudo verificar la cuenta</p>
              <p className="text-gray-600 text-sm mb-6 max-w-sm">
                {message}
              </p>
              <div className="space-y-3 w-full">
                <Link
                  to="/login"
                  className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 transition-colors"
                >
                  Volver al inicio de sesión
                </Link>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;
