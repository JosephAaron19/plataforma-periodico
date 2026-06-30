import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, Building2, AlertCircle } from 'lucide-react';
import api from '../../services/api';

interface Plan {
  id: number;
  nombre: string;
  precio: string;
  caracteristicas: string[];
  recomendado?: boolean;
}

const SelectPlan: React.FC = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch public plans from API
    const fetchPlans = async () => {
      try {
        const response = await api.get('/plans/public/');
        // Mapping backend response or using mock data if unavailable
        if (response.data && response.data.length > 0) {
          setPlans(response.data);
        } else {
          loadMockPlans();
        }
      } catch (err) {
        console.warn("Could not fetch plans, loading mocks.", err);
        loadMockPlans();
      } finally {
        setIsLoading(false);
      }
    };
    fetchPlans();
  }, []);

  const loadMockPlans = () => {
    setPlans([
      { id: 1, nombre: 'Free', precio: '0.00', caracteristicas: ['1 Empresa', '5 Ediciones', 'Visor Estándar'] },
      { id: 2, nombre: 'Pro', precio: '49.00', caracteristicas: ['3 Empresas', 'Ediciones Ilimitadas', 'Visor Premium'], recomendado: true },
      { id: 3, nombre: 'Business', precio: '199.00', caracteristicas: ['Ilimitadas', 'Marca de agua', 'Soporte 24/7'] }
    ]);
  };

  const handleSelectPlan = async (planId: number) => {
    setIsSubmitting(true);
    setError('');
    try {
      // POST /api/plans/subscribe
      await api.post('/plans/subscribe/', { plan_id: planId });
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.error || 'No se pudo seleccionar el plan.');
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center bg-gray-50">Cargando planes...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-16 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center justify-center p-2 bg-brand-100 rounded-full mb-4">
            <Building2 className="h-6 w-6 text-brand-600" />
          </div>
          <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            Elige el plan ideal para tu editorial
          </h2>
          <p className="mt-4 text-lg text-gray-500">
            Paso 2 de 2. Puedes empezar gratis y mejorar tu plan cuando tu negocio lo requiera.
          </p>
        </div>

        {error && (
          <div className="max-w-3xl mx-auto mb-8 bg-red-50 border-l-4 border-red-500 p-4 rounded-md flex items-start">
            <AlertCircle className="h-5 w-5 text-red-500 mr-3 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan) => (
            <div 
              key={plan.id} 
              className={`relative flex flex-col p-8 rounded-3xl transition-transform ${
                plan.recomendado 
                  ? 'bg-dark-900 text-white shadow-2xl scale-105 ring-4 ring-brand-500 ring-opacity-50' 
                  : 'bg-white text-gray-900 border border-gray-200 shadow-sm hover:shadow-md'
              }`}
            >
              {plan.recomendado && (
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-gradient-to-r from-brand-400 to-brand-600 text-white px-4 py-1 rounded-full text-xs font-bold uppercase tracking-widest shadow-sm">
                  Más Popular
                </div>
              )}
              
              <div className="mb-6">
                <h3 className="text-2xl font-bold">{plan.nombre}</h3>
                <div className="mt-4 flex items-baseline text-5xl font-extrabold">
                  ${plan.precio}
                  <span className={`ml-1 text-xl font-medium ${plan.recomendado ? 'text-gray-400' : 'text-gray-500'}`}>/mes</span>
                </div>
              </div>

              <ul className="flex-1 space-y-4 mb-8">
                {plan.caracteristicas.map((feat, j) => (
                  <li key={j} className="flex items-center">
                    <CheckCircle2 className={`h-5 w-5 mr-3 flex-shrink-0 ${plan.recomendado ? 'text-brand-400' : 'text-brand-500'}`} />
                    <span className="text-sm">{feat}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleSelectPlan(plan.id)}
                disabled={isSubmitting}
                className={`w-full py-4 px-6 rounded-xl text-center font-bold text-lg transition-all disabled:opacity-70 ${
                  plan.recomendado 
                    ? 'bg-brand-500 hover:bg-brand-400 text-white shadow-lg shadow-brand-500/30' 
                    : 'bg-brand-50 text-brand-700 hover:bg-brand-100'
                }`}
              >
                {isSubmitting ? 'Procesando...' : 'Seleccionar Plan'}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SelectPlan;
