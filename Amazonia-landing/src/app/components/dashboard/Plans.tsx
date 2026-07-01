import React, { useState, useEffect } from 'react';
import { 
  Building2, Users, BookCopy, Database, Calendar, 
  AlertCircle, Check, CheckCircle2, RefreshCw, 
  ArrowRight, ShieldAlert, AlertTriangle, ArrowUpRight,
  Plus, Pencil, Trash2, X, Globe, Lock, Info, PlusCircle, Trash
} from 'lucide-react';
import { useAuth } from '../../contexts/auth';
import api from '../../services/api';
import { toast } from 'sonner';

interface PlanFuncionalidad {
  id?: number;
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

interface UsageMetric {
  limit: number | null;
  used: number;
  available: number | null;
}

interface StorageUsageMetric {
  limit_bytes: number | null;
  used_bytes: number;
  available_bytes: number | null;
}

interface CompanyPlanUsage {
  plan: {
    code: string;
    name: string;
  };
  users: UsageMetric;
  editions: UsageMetric;
  storage: StorageUsageMetric;
}

const Plans: React.FC = () => {
  const { activeCompanyId } = useAuth();
  
  // State
  const [catalog, setCatalog] = useState<Plan[]>([]);
  const [usage, setUsage] = useState<CompanyPlanUsage | null>(null);
  
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Modal state for Create / Edit
  const [showFormModal, setShowFormModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [submittingPlan, setSubmittingPlan] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form State
  const [codigo, setCodigo] = useState('');
  const [nombre, setNombre] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [precio, setPrecio] = useState('0.00');
  const [moneda, setMoneda] = useState('PEN');
  const [periodicidad, setPeriodicidad] = useState('MENSUAL');
  
  // Limits
  const [hasUserLimit, setHasUserLimit] = useState(true);
  const [limiteUsuarios, setLimiteUsuarios] = useState('10');
  
  const [hasEditionLimit, setHasEditionLimit] = useState(true);
  const [limiteEdicionesMes, setLimiteEdicionesMes] = useState('15');
  
  const [hasStorageLimit, setHasStorageLimit] = useState(true);
  const [limiteStorageMb, setLimiteStorageMb] = useState('500');
  
  const [hasPdfLimit, setHasPdfLimit] = useState(true);
  const [limitePdfMb, setLimitePdfMb] = useState('30');
  
  const [hasPageLimit, setHasPageLimit] = useState(true);
  const [limitePaginasPdf, setLimitePaginasPdf] = useState('100');

  // Plan general status
  const [esPublico, setEsPublico] = useState(true);
  const [orden, setOrden] = useState('0');
  const [estado, setEstado] = useState('ACTIVO');

  // Plan Functionalities (Items visible on Landing Page)
  const [funcionalidades, setFuncionalidades] = useState<PlanFuncionalidad[]>([]);
  const [newFeatureName, setNewFeatureName] = useState('');
  const [newFeatureDesc, setNewFeatureDesc] = useState('');

  // Modal state for Delete confirmation
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [planToDelete, setPlanToDelete] = useState<Plan | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch all data
  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // 1. Fetch Plan Catalog for Admin Panel (lists all active and inactive, public & private)
      try {
        const response = await api.get('/plans/admin/');
        setCatalog(response.data || []);
      } catch (err: any) {
        console.warn("Could not fetch admin plan catalog, falling back to public plans:", err);
        try {
          const publicResponse = await api.get('/plans/');
          setCatalog(publicResponse.data || []);
        } catch (pubErr) {
          console.error("Could not fetch catalog from API, loading mocks.", pubErr);
          loadMockCatalog();
        }
      }

      // 2. Fetch Active Company usage (if company id exists)
      if (activeCompanyId) {
        try {
          const usageResponse = await api.get(`/companies/${activeCompanyId}/plan/usage/`);
          setUsage(usageResponse.data);
        } catch (err: any) {
          console.warn("Could not fetch active company plan usage:", err);
          setUsage(null);
        }
      }

    } catch (err: any) {
      setError("Ocurrió un error al sincronizar la información del módulo.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadMockCatalog = () => {
    setCatalog([
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
          { codigo_funcionalidad: "FEAT_ACCESO_DIA", nombre: "Acceso a la edición del día", descripcion: "Permite leer la edición digital publicada hoy", habilitada: true },
          { codigo_funcionalidad: "FEAT_LECTURA_LINEA", nombre: "Lectura en línea", descripcion: "Permite leer en el visor digital sin descargar", habilitada: true },
          { codigo_funcionalidad: "FEAT_MULTIDISPOSITIVO", nombre: "Desde cualquier dispositivo", descripcion: "Acceso optimizado para PC, tablets y móviles", habilitada: true }
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
          { codigo_funcionalidad: "FEAT_ACCESO_COMPLETO", nombre: "Acceso completo a todas las ediciones", descripcion: "Acceso irrestricto a publicaciones", habilitada: true },
          { codigo_funcionalidad: "FEAT_HISTORIAL", nombre: "Historial de ediciones", descripcion: "Acceso al catálogo histórico completo", habilitada: true },
          { codigo_funcionalidad: "FEAT_LECTURA_ILIMITADA", nombre: "Lectura sin límites", descripcion: "Sin límites de visualización de páginas", habilitada: true },
          { codigo_funcionalidad: "FEAT_MULTIDISPOSITIVO", nombre: "Desde cualquier dispositivo", descripcion: "Acceso optimizado para PC, tablets y móviles", habilitada: true },
          { codigo_funcionalidad: "FEAT_SOPORTE_PRIO", nombre: "Soporte prioritario", descripcion: "Atención preferente en consultas de soporte técnico", habilitada: true }
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
          { codigo_funcionalidad: "FEAT_ACCESO_COMPLETO", nombre: "Acceso completo a todas las ediciones", descripcion: "Acceso irrestricto a publicaciones", habilitada: true },
          { codigo_funcionalidad: "FEAT_HISTORIAL", nombre: "Historial de ediciones", descripcion: "Acceso al catálogo histórico completo", habilitada: true },
          { codigo_funcionalidad: "FEAT_LECTURA_ILIMITADA", nombre: "Lectura sin límites", descripcion: "Sin límites de visualización de páginas", habilitada: true },
          { codigo_funcionalidad: "FEAT_MULTIDISPOSITIVO", nombre: "Desde cualquier dispositivo", descripcion: "Acceso optimizado para PC, tablets y móviles", habilitada: true },
          { codigo_funcionalidad: "FEAT_SOPORTE_PRIO", nombre: "Soporte prioritario", descripcion: "Atención preferente en consultas de soporte técnico", habilitada: true },
          { codigo_funcionalidad: "FEAT_PROMO_GRATIS", nombre: "2 meses gratis", descripcion: "Ahorro equivalente a dos mensualidades completas", habilitada: true }
        ]
      }
    ]);
  };

  useEffect(() => {
    fetchData();
  }, [activeCompanyId]);

  // Open Form modal for Create
  const handleOpenCreateModal = () => {
    setIsEditing(false);
    setCodigo('');
    setNombre('');
    setDescripcion('');
    setPrecio('0.00');
    setMoneda('PEN');
    setPeriodicidad('MENSUAL');
    
    setHasUserLimit(true);
    setLimiteUsuarios('10');
    
    setHasEditionLimit(true);
    setLimiteEdicionesMes('15');
    
    setHasStorageLimit(true);
    setLimiteStorageMb('500');
    
    setHasPdfLimit(true);
    setLimitePdfMb('30');
    
    setHasPageLimit(true);
    setLimitePaginasPdf('100');
    
    setEsPublico(true);
    setOrden('0');
    setEstado('ACTIVO');
    setFuncionalidades([]);
    setNewFeatureName('');
    setNewFeatureDesc('');
    
    setFormError(null);
    setShowFormModal(true);
  };

  // Open Form modal for Edit
  const handleOpenEditModal = (plan: Plan) => {
    setIsEditing(true);
    setCodigo(plan.codigo);
    setNombre(plan.nombre);
    setDescripcion(plan.descripcion || '');
    setPrecio(plan.precio);
    setMoneda(plan.moneda);
    setPeriodicidad(plan.periodicidad);
    
    setHasUserLimit(plan.limite_usuarios !== null);
    setLimiteUsuarios(plan.limite_usuarios !== null ? plan.limite_usuarios.toString() : '');
    
    setHasEditionLimit(plan.limite_ediciones_mes !== null);
    setLimiteEdicionesMes(plan.limite_ediciones_mes !== null ? plan.limite_ediciones_mes.toString() : '');
    
    setHasStorageLimit(plan.limite_storage_mb !== null);
    setLimiteStorageMb(plan.limite_storage_mb !== null ? plan.limite_storage_mb.toString() : '');
    
    setHasPdfLimit(plan.limite_pdf_mb !== null);
    setLimitePdfMb(plan.limite_pdf_mb !== null ? plan.limite_pdf_mb.toString() : '');
    
    setHasPageLimit(plan.limite_paginas_pdf !== null);
    setLimitePaginasPdf(plan.limite_paginas_pdf !== null ? plan.limite_paginas_pdf.toString() : '');
    
    setEsPublico(plan.es_publico);
    setOrden(plan.orden.toString());
    setEstado(plan.estado);
    setFuncionalidades(plan.funcionalidades || []);
    setNewFeatureName('');
    setNewFeatureDesc('');
    
    setFormError(null);
    setShowFormModal(true);
  };

  // Add functionality item to local form state
  const handleAddFeature = () => {
    if (!newFeatureName.trim()) {
      toast.error("El nombre del ítem es obligatorio.");
      return;
    }
    
    // Generate code from name
    const generatedCode = 'FEAT_' + newFeatureName
      .trim()
      .toUpperCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "") // Remove accents
      .replace(/[^A-Z0-9\s]/g, "") // Remove special characters
      .replace(/\s+/g, "_") // Replace spaces with underscores
      .substring(0, 50);

    const newItem: PlanFuncionalidad = {
      codigo_funcionalidad: generatedCode,
      nombre: newFeatureName.trim(),
      descripcion: newFeatureDesc.trim() || null,
      habilitada: true
    };

    setFuncionalidades([...funcionalidades, newItem]);
    setNewFeatureName('');
    setNewFeatureDesc('');
  };

  // Remove functionality item from local form state
  const handleRemoveFeature = (index: number) => {
    const updated = [...funcionalidades];
    updated.splice(index, 1);
    setFuncionalidades(updated);
  };

  // Submit Plan Form
  const handleSubmitPlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!codigo.trim() || !nombre.trim()) {
      setFormError("El código y el nombre del plan son obligatorios.");
      return;
    }

    setSubmittingPlan(true);
    setFormError(null);

    const payload = {
      codigo: codigo.trim().toUpperCase(),
      nombre: nombre.trim(),
      descripcion: descripcion.trim() || null,
      precio: parseFloat(precio) || 0,
      moneda,
      periodicidad,
      limite_usuarios: hasUserLimit ? (parseInt(limiteUsuarios, 10) || null) : null,
      limite_ediciones_mes: hasEditionLimit ? (parseInt(limiteEdicionesMes, 10) || null) : null,
      limite_storage_mb: hasStorageLimit ? (parseInt(limiteStorageMb, 10) || null) : null,
      limite_pdf_mb: hasPdfLimit ? (parseInt(limitePdfMb, 10) || null) : null,
      limite_paginas_pdf: hasPageLimit ? (parseInt(limitePaginasPdf, 10) || null) : null,
      es_publico: esPublico,
      orden: parseInt(orden, 10) || 0,
      estado,
      funcionalidades
    };

    try {
      if (isEditing) {
        await api.put(`/plans/admin/${codigo}/`, payload);
        toast.success(`El plan "${nombre}" se ha actualizado correctamente.`);
      } else {
        await api.post('/plans/admin/', payload);
        toast.success(`El plan "${nombre}" ha sido creado con éxito.`);
      }
      setShowFormModal(false);
      fetchData();
    } catch (err: any) {
      console.error(err);
      if (err.response?.status === 403) {
        setFormError("No tienes permisos suficientes de Superadministrador para guardar planes.");
      } else {
        const errors = err.response?.data;
        if (errors && typeof errors === 'object') {
          const text = Object.entries(errors)
            .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
            .join(' | ');
          setFormError(text);
        } else {
          setFormError("Ocurrió un error al intentar guardar el plan.");
        }
      }
    } finally {
      setSubmittingPlan(false);
    }
  };

  // Open Delete confirmation
  const handleOpenDeleteModal = (plan: Plan) => {
    setPlanToDelete(plan);
    setShowDeleteModal(true);
  };

  const handleConfirmDelete = async () => {
    if (!planToDelete) return;
    setIsDeleting(true);
    try {
      await api.delete(`/plans/admin/${planToDelete.codigo}/`);
      toast.success(`El plan "${planToDelete.nombre}" ha sido eliminado.`);
      setShowDeleteModal(false);
      fetchData();
    } catch (err: any) {
      console.error(err);
      if (err.response?.status === 403) {
        toast.error("No tienes permisos de Superadministrador para eliminar planes.");
      } else {
        toast.error(err.response?.data?.detail || "No se pudo eliminar el plan. Podría estar asignado a alguna empresa o usuario.");
      }
    } finally {
      setIsDeleting(false);
    }
  };

  // Helpers for limits rendering
  const formatLimit = (value: number | null, suffix = '') => {
    if (value === null) return 'Ilimitado';
    return `${value} ${suffix}`;
  };

  const formatStorageMB = (mb: number | null) => {
    if (mb === null) return 'Ilimitado';
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(1)} GB`;
    }
    return `${mb} MB`;
  };

  const getPercentage = (used: number, limit: number | null) => {
    if (limit === null || limit <= 0) return 0;
    return Math.min(Math.round((used / limit) * 100), 100);
  };

  const formatStorage = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(2)} GB`;
    }
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 text-left">
      
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-3xl shadow-xs border border-gray-100">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestión de Planes de Suscripción</h1>
          <p className="text-gray-500 mt-1">
            Administra los planes que ven los lectores en la Landing Page, define límites y añade los ítems/beneficios correspondientes de la oferta comercial.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2.5 border border-gray-200 rounded-2xl hover:bg-gray-50 text-gray-700 font-semibold text-sm transition-colors shadow-xs"
          >
            <RefreshCw className="h-4 w-4" />
            Sincronizar
          </button>
          
          <button 
            onClick={handleOpenCreateModal}
            className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-bold text-sm shadow-md shadow-emerald-600/10 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Crear Plan
          </button>
        </div>
      </div>

      {/* active company statistics meter (collapsible/summarized for visibility) */}
      {usage && (
        <div className="bg-white p-6 rounded-3xl shadow-xs border border-gray-100 space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-md font-bold text-gray-900 flex items-center gap-2">
                <Building2 className="h-5 w-5 text-emerald-600" />
                Límites y Consumo de tu Empresa Activa ({usage.plan.name})
              </h3>
              <p className="text-xs text-gray-400">Estado de recursos en tiempo real en la editorial actual</p>
            </div>
            <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-100">
              Plan: {usage.plan.code}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
            
            {/* Users Meter */}
            <div className="bg-gray-50/50 p-4 rounded-2xl border border-gray-100">
              <div className="flex justify-between text-xs font-bold text-gray-700 mb-1">
                <span>Miembros</span>
                <span>{usage.users.used} / {formatLimit(usage.users.limit)}</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-emerald-500 transition-all"
                  style={{ width: `${getPercentage(usage.users.used, usage.users.limit)}%` }}
                ></div>
              </div>
            </div>

            {/* Editions Meter */}
            <div className="bg-gray-50/50 p-4 rounded-2xl border border-gray-100">
              <div className="flex justify-between text-xs font-bold text-gray-700 mb-1">
                <span>Ediciones/Mes</span>
                <span>{usage.editions.used} / {formatLimit(usage.editions.limit)}</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-emerald-500 transition-all"
                  style={{ width: `${getPercentage(usage.editions.used, usage.editions.limit)}%` }}
                ></div>
              </div>
            </div>

            {/* Storage Meter */}
            <div className="bg-gray-50/50 p-4 rounded-2xl border border-gray-100">
              <div className="flex justify-between text-xs font-bold text-gray-700 mb-1">
                <span>Almacenamiento</span>
                <span>{formatStorage(usage.storage.used_bytes)} / {usage.storage.limit_bytes ? formatStorage(usage.storage.limit_bytes) : 'Ilimitado'}</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-emerald-500 transition-all"
                  style={{ width: `${getPercentage(usage.storage.used_bytes, usage.storage.limit_bytes)}%` }}
                ></div>
              </div>
            </div>

          </div>
        </div>
      )}

      {/* Plan CRUD Table */}
      <div className="bg-white rounded-3xl shadow-xs border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h3 className="text-lg font-bold text-gray-900">Catálogo de Suscripciones Registradas</h3>
          <p className="text-xs text-gray-400 mt-1">Los planes listados a continuación representan los paquetes comerciales vigentes.</p>
        </div>

        {catalog.length === 0 ? (
          <div className="p-12 text-center text-gray-500 font-medium">
            No hay planes registrados en el catálogo. Utiliza el botón superior para crear uno nuevo.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-50 text-left text-xs font-bold text-gray-500 border-b border-gray-100">
                  <th className="py-4 px-6">Orden / Plan / Código</th>
                  <th className="py-4 px-6">Precio & Facturación</th>
                  <th className="py-4 px-6">Beneficios e Ítems en Landing</th>
                  <th className="py-4 px-6">Límites Internos (Usr / Edic / Disc)</th>
                  <th className="py-4 px-6 text-center">Visibilidad</th>
                  <th className="py-4 px-6 text-center">Estado</th>
                  <th className="py-4 px-6 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm">
                {catalog.map((plan) => (
                  <tr key={plan.codigo} className="hover:bg-gray-50/50 transition-colors align-top">
                    
                    {/* Name & Code */}
                    <td className="py-4 px-6">
                      <div className="flex items-start gap-3">
                        <span className="font-bold text-xs text-gray-400 bg-gray-100 h-6 w-6 flex items-center justify-center rounded-lg mt-1">
                          {plan.orden}
                        </span>
                        <div>
                          <p className="font-bold text-gray-900">{plan.nombre}</p>
                          <p className="text-xs font-semibold text-emerald-600 mt-0.5 tracking-wider uppercase">{plan.codigo}</p>
                          <p className="text-xs text-gray-400 mt-1 max-w-[200px] leading-relaxed italic">{plan.descripcion}</p>
                        </div>
                      </div>
                    </td>

                    {/* Price */}
                    <td className="py-4 px-6">
                      <div className="font-bold text-gray-900">
                        {plan.moneda} {Number(plan.precio).toFixed(2)}
                      </div>
                      <p className="text-xs text-gray-400 font-medium capitalize mt-0.5">
                        {plan.periodicidad.toLowerCase()}
                      </p>
                    </td>

                    {/* Items on Landing (Funcionalidades) */}
                    <td className="py-4 px-6">
                      {plan.funcionalidades && plan.funcionalidades.length > 0 ? (
                        <ul className="space-y-1 max-w-[280px]">
                          {plan.funcionalidades.map((feat) => (
                            <li key={feat.codigo_funcionalidad} className="flex items-start gap-1.5 text-xs text-gray-600">
                              <CheckCircle2 size={13} className="text-emerald-600 mt-0.5 flex-shrink-0" />
                              <span className="font-medium text-gray-700">
                                {feat.nombre}
                              </span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <span className="text-xs text-gray-400 font-semibold italic">Sin beneficios listados</span>
                      )}
                    </td>

                    {/* Basic resource limits */}
                    <td className="py-4 px-6 space-y-1">
                      <p className="text-xs text-gray-600 font-semibold">
                        Usuarios: <strong className="text-gray-900">{formatLimit(plan.limite_usuarios)}</strong>
                      </p>
                      <p className="text-xs text-gray-600 font-semibold">
                        Ediciones/Mes: <strong className="text-gray-900">{formatLimit(plan.limite_ediciones_mes)}</strong>
                      </p>
                      <p className="text-xs text-gray-600 font-semibold">
                        Almacenamiento: <strong className="text-gray-900">{formatStorageMB(plan.limite_storage_mb)}</strong>
                      </p>
                    </td>

                    {/* Visibility status */}
                    <td className="py-4 px-6 text-center">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold border ${
                        plan.es_publico 
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                          : 'bg-slate-50 text-slate-600 border-slate-200'
                      }`}>
                        {plan.es_publico ? (
                          <>
                            <Globe className="h-3 w-3" />
                            Público
                          </>
                        ) : (
                          <>
                            <Lock className="h-3 w-3" />
                            Privado
                          </>
                        )}
                      </span>
                    </td>

                    {/* Active State */}
                    <td className="py-4 px-6 text-center">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold border ${
                        plan.estado === 'ACTIVO' 
                          ? 'bg-green-50 text-green-700 border-green-200' 
                          : 'bg-red-50 text-red-700 border-red-200'
                      }`}>
                        {plan.estado}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleOpenEditModal(plan)}
                          className="p-2 border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-gray-950 rounded-xl transition-all shadow-xs"
                          title="Editar Plan"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        
                        <button
                          onClick={() => handleOpenDeleteModal(plan)}
                          className="p-2 border border-red-100 text-red-600 hover:bg-red-50 hover:text-red-700 rounded-xl transition-all shadow-xs"
                          title="Eliminar Plan"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* CREATE / EDIT FORM MODAL */}
      {showFormModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl shadow-xl max-w-4xl w-full overflow-hidden border border-slate-100 text-left animate-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">
            
            <div className="p-6 border-b border-gray-100 flex items-center justify-between flex-shrink-0">
              <h3 className="text-lg font-bold text-gray-900">
                {isEditing ? `Editar Plan "${nombre}"` : 'Crear Nuevo Plan de Suscripción'}
              </h3>
              <button 
                onClick={() => setShowFormModal(false)}
                className="text-gray-400 hover:text-gray-600 text-xl font-bold p-1"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleSubmitPlan} className="flex-1 overflow-y-auto p-6 space-y-6">
              
              {formError && (
                <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex gap-3 text-sm text-red-700">
                  <ShieldAlert className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div className="font-semibold">{formError}</div>
                </div>
              )}

              {/* General Metadata section */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest border-b pb-1">1. Datos Generales</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1.5">
                      Código Único <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={codigo}
                      onChange={(e) => setCodigo(e.target.value)}
                      placeholder="PLAN_PREMIUM"
                      disabled={isEditing}
                      className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:bg-white transition-all font-semibold uppercase disabled:opacity-50"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1.5">
                      Nombre Comercial <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={nombre}
                      onChange={(e) => setNombre(e.target.value)}
                      placeholder="Plan Premium"
                      className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:bg-white transition-all font-semibold"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1.5">Descripción o Eslogan</label>
                  <textarea
                    value={descripcion}
                    onChange={(e) => setDescripcion(e.target.value)}
                    placeholder="Describe los alcances y ventajas comerciales de este plan."
                    rows={2}
                    className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:bg-white transition-all font-semibold"
                  />
                </div>
              </div>

              {/* Commercial price & period section */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest border-b pb-1">2. Costo y Facturación</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1.5">Moneda</label>
                    <select
                      value={moneda}
                      onChange={(e) => setMoneda(e.target.value)}
                      className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 focus:outline-none focus:border-emerald-500 focus:bg-white font-semibold"
                    >
                      <option value="PEN">Soles (PEN)</option>
                      <option value="USD">Dólares (USD)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1.5">Monto o Tarifa</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={precio}
                      onChange={(e) => setPrecio(e.target.value)}
                      className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 focus:outline-none focus:border-emerald-500 focus:bg-white font-semibold"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1.5">Periodicidad</label>
                    <select
                      value={periodicidad}
                      onChange={(e) => setPeriodicidad(e.target.value)}
                      className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 focus:outline-none focus:border-emerald-500 focus:bg-white font-semibold"
                    >
                      <option value="MENSUAL">Mensual</option>
                      <option value="ANUAL">Anual</option>
                      <option value="SEMESTRAL">Semestral</option>
                      <option value="PERSONALIZADO">Personalizado (Diario/Edición)</option>
                      <option value="UNICO">Pago Único</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Items seen on Landing Page (Funcionalidades) */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest border-b pb-1">3. Beneficios e Ítems en la Landing Page</h4>
                
                {/* List of current features */}
                <div className="space-y-2">
                  <label className="block text-xs font-bold text-gray-700">Beneficios definidos para este plan</label>
                  {funcionalidades.length === 0 ? (
                    <div className="p-3 bg-gray-50 border border-gray-200 rounded-2xl text-xs text-gray-400 font-semibold italic text-center">
                      No se han agregado ítems para mostrar en el catálogo. Agrega beneficios abajo.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {funcionalidades.map((feat, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-2xl text-xs">
                          <div>
                            <p className="font-bold text-slate-800">{feat.nombre}</p>
                            <p className="text-[10px] text-slate-400 font-semibold tracking-wider mt-0.5">{feat.codigo_funcionalidad}</p>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleRemoveFeature(index)}
                            className="p-1 text-red-500 hover:text-red-700 transition-colors"
                          >
                            <Trash size={15} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Inline form to add new feature */}
                <div className="bg-slate-50 p-4 border border-slate-200 rounded-2xl space-y-3">
                  <div className="text-xs font-bold text-slate-700 flex items-center gap-1">
                    <PlusCircle size={15} className="text-emerald-600" />
                    Añadir Ítem de Beneficio / Característica
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <input
                      type="text"
                      placeholder="Ej: Acceso completo a todas las ediciones"
                      value={newFeatureName}
                      onChange={(e) => setNewFeatureName(e.target.value)}
                      className="bg-white border border-gray-200 rounded-xl p-2.5 text-xs text-gray-700 placeholder-slate-400 font-semibold"
                    />
                    <input
                      type="text"
                      placeholder="Ej: Descripción interna breve (opcional)"
                      value={newFeatureDesc}
                      onChange={(e) => setNewFeatureDesc(e.target.value)}
                      className="bg-white border border-gray-200 rounded-xl p-2.5 text-xs text-gray-700 placeholder-slate-400 font-semibold"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleAddFeature}
                    className="px-4 py-2 bg-slate-200 hover:bg-slate-350 text-slate-800 font-bold text-xs rounded-xl flex items-center gap-1.5 transition-colors self-start"
                  >
                    <Plus size={14} />
                    Agregar Ítem al Plan
                  </button>
                </div>
              </div>

              {/* Resource Limits setup */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest border-b pb-1">4. Límites y Consumos de la Empresa</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* Limit users */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-gray-700">Límite de Miembros de Equipo</label>
                      <label className="inline-flex items-center gap-1.5 cursor-pointer text-xs font-bold text-gray-500">
                        <input
                          type="checkbox"
                          checked={hasUserLimit}
                          onChange={(e) => setHasUserLimit(e.target.checked)}
                          className="rounded text-emerald-600 focus:ring-emerald-500"
                        />
                        Definir límite
                      </label>
                    </div>
                    <input
                      type="number"
                      disabled={!hasUserLimit}
                      value={limiteUsuarios}
                      onChange={(e) => setLimiteUsuarios(e.target.value)}
                      placeholder="Ej: 10"
                      className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 focus:outline-none focus:border-emerald-500 focus:bg-white disabled:opacity-40 font-semibold"
                    />
                  </div>

                  {/* Limit editions */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-gray-700">Límite de Ediciones al Mes</label>
                      <label className="inline-flex items-center gap-1.5 cursor-pointer text-xs font-bold text-gray-500">
                        <input
                          type="checkbox"
                          checked={hasEditionLimit}
                          onChange={(e) => setHasEditionLimit(e.target.checked)}
                          className="rounded text-emerald-600 focus:ring-emerald-500"
                        />
                        Definir límite
                      </label>
                    </div>
                    <input
                      type="number"
                      disabled={!hasEditionLimit}
                      value={limiteEdicionesMes}
                      onChange={(e) => setLimiteEdicionesMes(e.target.value)}
                      placeholder="Ej: 15"
                      className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 focus:outline-none focus:border-emerald-500 focus:bg-white disabled:opacity-40 font-semibold"
                    />
                  </div>

                  {/* Limit storage */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-gray-700">Límite Almacenamiento (MB)</label>
                      <label className="inline-flex items-center gap-1.5 cursor-pointer text-xs font-bold text-gray-500">
                        <input
                          type="checkbox"
                          checked={hasStorageLimit}
                          onChange={(e) => setHasStorageLimit(e.target.checked)}
                          className="rounded text-emerald-600 focus:ring-emerald-500"
                        />
                        Definir límite
                      </label>
                    </div>
                    <input
                      type="number"
                      disabled={!hasStorageLimit}
                      value={limiteStorageMb}
                      onChange={(e) => setLimiteStorageMb(e.target.value)}
                      placeholder="Ej: 1024"
                      className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 focus:outline-none focus:border-emerald-500 focus:bg-white disabled:opacity-40 font-semibold"
                    />
                  </div>

                  {/* Limit PDF MB */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-gray-700">Tamaño PDF Máximo (MB)</label>
                      <label className="inline-flex items-center gap-1.5 cursor-pointer text-xs font-bold text-gray-500">
                        <input
                          type="checkbox"
                          checked={hasPdfLimit}
                          onChange={(e) => setHasPdfLimit(e.target.checked)}
                          className="rounded text-emerald-600 focus:ring-emerald-500"
                        />
                        Definir límite
                      </label>
                    </div>
                    <input
                      type="number"
                      disabled={!hasPdfLimit}
                      value={limitePdfMb}
                      onChange={(e) => setLimitePdfMb(e.target.value)}
                      placeholder="Ej: 50"
                      className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 focus:outline-none focus:border-emerald-500 focus:bg-white disabled:opacity-40 font-semibold"
                    />
                  </div>

                  {/* Limit Pages PDF */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-gray-700">Páginas Máximas por PDF</label>
                      <label className="inline-flex items-center gap-1.5 cursor-pointer text-xs font-bold text-gray-500">
                        <input
                          type="checkbox"
                          checked={hasPageLimit}
                          onChange={(e) => setHasPageLimit(e.target.checked)}
                          className="rounded text-emerald-600 focus:ring-emerald-500"
                        />
                        Definir límite
                      </label>
                    </div>
                    <input
                      type="number"
                      disabled={!hasPageLimit}
                      value={limitePaginasPdf}
                      onChange={(e) => setLimitePaginasPdf(e.target.value)}
                      placeholder="Ej: 150"
                      className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 focus:outline-none focus:border-emerald-500 focus:bg-white disabled:opacity-40 font-semibold"
                    />
                  </div>

                </div>
              </div>

              {/* Status and Order section */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest border-b pb-1">5. Publicación y Configuración</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1.5">Orden de Visualización</label>
                    <input
                      type="number"
                      value={orden}
                      onChange={(e) => setOrden(e.target.value)}
                      className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 focus:outline-none focus:border-emerald-500 focus:bg-white font-semibold"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1.5">Visibilidad Landing</label>
                    <select
                      value={esPublico ? 'true' : 'false'}
                      onChange={(e) => setEsPublico(e.target.value === 'true')}
                      className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 focus:outline-none focus:border-emerald-500 focus:bg-white font-semibold"
                    >
                      <option value="true">Público (Visible)</option>
                      <option value="false">Privado (Solo Admin)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1.5">Estado del Plan</label>
                    <select
                      value={estado}
                      onChange={(e) => setEstado(e.target.value)}
                      className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 focus:outline-none focus:border-emerald-500 focus:bg-white font-semibold"
                    >
                      <option value="ACTIVO">Activo</option>
                      <option value="INACTIVO">Inactivo</option>
                    </select>
                  </div>
                </div>
              </div>

            </form>

            <div className="p-6 bg-gray-50 border-t border-gray-100 flex justify-end gap-3 flex-shrink-0">
              <button
                type="button"
                onClick={() => setShowFormModal(false)}
                disabled={submittingPlan}
                className="px-4 py-2.5 bg-white border border-gray-200 rounded-2xl hover:bg-gray-100 text-gray-700 font-semibold text-sm transition-colors"
              >
                Cancelar
              </button>
              
              <button
                type="button"
                onClick={handleSubmitPlan}
                disabled={submittingPlan}
                className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-bold text-sm shadow-md shadow-emerald-600/10 transition-colors disabled:opacity-50"
              >
                {submittingPlan ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Guardando...
                  </>
                ) : (
                  <>
                    Guardar Cambios
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>

          </div>
        </div>
      )}

      {/* DELETE CONFIRMATION MODAL */}
      {showDeleteModal && planToDelete && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl shadow-xl max-w-md w-full overflow-hidden border border-slate-100 text-left animate-in zoom-in-95 duration-200">
            
            <div className="p-6 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                Eliminar Plan de Suscripción
              </h3>
              <button 
                onClick={() => setShowDeleteModal(false)}
                className="text-gray-400 hover:text-gray-600 text-xl font-bold p-1"
              >
                &times;
              </button>
            </div>

            <div className="p-6 space-y-3">
              <p className="text-sm text-gray-600 font-semibold leading-relaxed">
                ¿Estás completamente seguro de que deseas eliminar el plan <strong className="text-gray-900">"{planToDelete.nombre}" ({planToDelete.codigo})</strong>?
              </p>
              <div className="p-3 bg-amber-50 border border-amber-100 text-xs text-amber-800 rounded-xl flex gap-2">
                <Info className="h-4.5 w-4.5 text-amber-600 flex-shrink-0" />
                <span>
                  <strong>Nota Importante:</strong> Esta acción no podrá completarse si existen empresas suscritas a este plan activo en el historial. Asegúrate de reasignarlas previamente.
                </span>
              </div>
            </div>

            <div className="p-6 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowDeleteModal(false)}
                disabled={isDeleting}
                className="px-4 py-2.5 bg-white border border-gray-200 rounded-2xl hover:bg-gray-100 text-gray-700 font-semibold text-sm transition-colors"
              >
                Cancelar
              </button>
              
              <button
                type="button"
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="px-5 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-2xl font-bold text-sm shadow-md shadow-red-600/10 transition-colors disabled:opacity-50"
              >
                {isDeleting ? "Eliminando..." : "Eliminar Plan"}
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};

export default Plans;
