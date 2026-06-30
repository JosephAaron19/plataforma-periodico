import React from 'react';
import { useAuth } from '../../contexts/auth';
import { BookCopy, Eye, CreditCard, TrendingUp, Users } from 'lucide-react';

const DashboardOverview: React.FC = () => {
  const { user, companies, activeCompanyId } = useAuth();
  
  const activeCompany = companies.find(c => c.id === activeCompanyId);

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 text-left">
      
      {/* Header section */}
      <div className="flex justify-between items-end bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Bienvenido, {user?.nombres || user?.email}
          </h1>
          <p className="text-gray-500 mt-1">
            Resumen de la empresa <span className="font-semibold text-brand-600">{activeCompany?.nombre || 'Organización'}</span>
          </p>
        </div>
        <div className="hidden sm:block text-right">
          <div className="text-sm font-medium text-gray-500 mb-1">Plan Actual</div>
          <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-brand-100 text-brand-700">
            Pro Plan
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { title: 'Total Ediciones', value: '12', change: '+2', icon: BookCopy, color: 'text-blue-500', bg: 'bg-blue-50' },
          { title: 'Vistas Totales', value: '4,521', change: '+12%', icon: Eye, color: 'text-purple-500', bg: 'bg-purple-50' },
          { title: 'Ventas Mensuales', value: '$840.00', change: '+5%', icon: CreditCard, color: 'text-emerald-500', bg: 'bg-emerald-50' },
          { title: 'Lectores Activos', value: '89', change: '+12', icon: Users, color: 'text-orange-500', bg: 'bg-orange-50' },
        ].map((stat, i) => {
          const Icon = stat.icon;
          return (
            <div key={i} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 mb-1">{stat.title}</p>
                <h3 className="text-2xl font-bold text-gray-900">{stat.value}</h3>
                <div className="mt-2 flex items-center text-sm font-medium text-emerald-600">
                  <TrendingUp className="h-4 w-4 mr-1" />
                  {stat.change} desde el mes pasado
                </div>
              </div>
              <div className={`p-3 rounded-xl ${stat.bg}`}>
                <Icon className={`h-6 w-6 ${stat.color}`} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Activity Mock */}
      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-gray-900">Actividad Reciente</h3>
            <button className="text-sm font-medium text-brand-600 hover:text-brand-700 cursor-pointer">Ver todo</button>
          </div>
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer">
                <div className="flex items-center">
                  <div className="h-10 w-10 rounded-full bg-brand-100 text-brand-600 flex items-center justify-center mr-4">
                    <BookCopy className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 text-sm">Nueva edición publicada</p>
                    <p className="text-xs text-gray-500">Revista Tecnológica Vol {i}</p>
                  </div>
                </div>
                <div className="text-xs text-gray-400 font-medium">Hace {i}h</div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-6">Acciones Rápidas</h3>
          <div className="space-y-3">
            <button className="w-full text-left p-4 rounded-xl bg-brand-50 hover:bg-brand-100 text-brand-700 font-medium transition-colors border border-brand-100 flex justify-between items-center group cursor-pointer">
              Subir Nueva Edición
              <BookCopy className="h-5 w-5 opacity-70 group-hover:opacity-100 transition-opacity" />
            </button>
            <button className="w-full text-left p-4 rounded-xl bg-gray-50 hover:bg-gray-100 text-gray-700 font-medium transition-colors border border-gray-200 flex justify-between items-center group cursor-pointer">
              Gestionar Accesos
              <Users className="h-5 w-5 opacity-70 group-hover:opacity-100 transition-opacity" />
            </button>
            <button className="w-full text-left p-4 rounded-xl bg-gray-50 hover:bg-gray-100 text-gray-700 font-medium transition-colors border border-gray-200 flex justify-between items-center group cursor-pointer">
              Ver Reportes de Ventas
              <CreditCard className="h-5 w-5 opacity-70 group-hover:opacity-100 transition-opacity" />
            </button>
          </div>
        </div>
      </div>
      
    </div>
  );
};

export default DashboardOverview;
