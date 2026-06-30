import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, MapPin, Briefcase, ArrowRight, BookOpen } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';

const CreateCompany: React.FC = () => {
  const [nombre, setNombre] = useState('');
  const [pais, setPais] = useState('PE');
  const [tipoNegocio, setTipoNegocio] = useState('editorial');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const navigate = useNavigate();
  const { refreshUserData } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // POST /api/companies/create
      await api.post('/companies/create/', {
        nombre,
        pais,
        tipo_negocio: tipoNegocio
      });
      
      // Update global context with the new company
      await refreshUserData();
      
      // Redirect to select plan
      navigate('/onboarding/select-plan', { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.error || 'No se pudo crear la empresa. Intenta nuevamente.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="mb-8 flex items-center justify-center">
        <BookOpen className="h-8 w-8 text-brand-600 mr-2" />
        <span className="text-2xl font-bold text-gray-900">DigitalSaaS</span>
      </div>

      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-lg border border-gray-100">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900 mb-2">Configura tu Entorno</h2>
          <p className="text-sm text-gray-500">
            Para empezar a publicar, necesitamos crear tu perfil empresarial. (Paso 1 de 2)
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-md text-sm border border-red-200">
            {error}
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="nombre" className="block text-sm font-medium text-gray-700">Nombre de la Empresa / Editorial</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Building2 className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  id="nombre"
                  required
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  className="block w-full pl-10 py-3 border-gray-300 rounded-lg focus:ring-brand-500 focus:border-brand-500 bg-gray-50 border"
                  placeholder="Ej: Ediciones El Faro"
                />
              </div>
            </div>

            <div>
              <label htmlFor="pais" className="block text-sm font-medium text-gray-700">País de Operación</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MapPin className="h-5 w-5 text-gray-400" />
                </div>
                <select
                  id="pais"
                  required
                  value={pais}
                  onChange={(e) => setPais(e.target.value)}
                  className="block w-full pl-10 py-3 border-gray-300 rounded-lg focus:ring-brand-500 focus:border-brand-500 bg-gray-50 border"
                >
                  <option value="PE">Perú</option>
                  <option value="MX">México</option>
                  <option value="CO">Colombia</option>
                  <option value="CL">Chile</option>
                  <option value="ES">España</option>
                  <option value="OTHER">Otro</option>
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="tipoNegocio" className="block text-sm font-medium text-gray-700">Tipo de Negocio</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Briefcase className="h-5 w-5 text-gray-400" />
                </div>
                <select
                  id="tipoNegocio"
                  required
                  value={tipoNegocio}
                  onChange={(e) => setTipoNegocio(e.target.value)}
                  className="block w-full pl-10 py-3 border-gray-300 rounded-lg focus:ring-brand-500 focus:border-brand-500 bg-gray-50 border"
                >
                  <option value="editorial">Editorial / Imprenta</option>
                  <option value="revista">Revista Digital</option>
                  <option value="autor">Autor Independiente</option>
                  <option value="educacion">Institución Educativa</option>
                  <option value="corporativo">Corporativo</option>
                </select>
              </div>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-bold text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 transition-colors disabled:opacity-70"
            >
              {isLoading ? 'Creando Empresa...' : 'Continuar al Plan'}
              {!isLoading && <ArrowRight className="ml-2 h-5 w-5" />}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateCompany;
