import { useState, useEffect } from 'react'
import axios from 'axios'

interface HealthResponse {
  status: string
  service: string
  database: string
  redis: string
}

export default function App() {
  const [loading, setLoading] = useState(false)
  const [backendStatus, setBackendStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking')
  const [dbStatus, setDbStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking')
  const [redisStatus, setRedisStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [lastChecked, setLastChecked] = useState<string>('')

  // Resolve VITE_API_URL from environment or fallback to relative URL path
  const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

  const checkHealth = async () => {
    setLoading(true)
    setErrorMsg(null)
    setBackendStatus('checking')
    setDbStatus('checking')
    setRedisStatus('checking')

    try {
      const response = await axios.get<HealthResponse>(`${API_URL}/health/`, { timeout: 6000 })
      setBackendStatus('connected')
      setDbStatus(response.data.database === 'connected' ? 'connected' : 'disconnected')
      setRedisStatus(response.data.redis === 'connected' ? 'connected' : 'disconnected')
    } catch (error: any) {
      setBackendStatus('disconnected')
      setDbStatus('disconnected')
      setRedisStatus('disconnected')
      setErrorMsg(error.message || 'Error de conexión con el Backend API')
    } finally {
      setLoading(false)
      setLastChecked(new Date().toLocaleTimeString())
    }
  }

  useEffect(() => {
    checkHealth()
  }, [])

  const getStatusBadge = (status: 'connected' | 'disconnected' | 'checking' | 'active') => {
    switch (status) {
      case 'active':
      case 'connected':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-2 h-2 mr-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Activo / Conectado
          </span>
        )
      case 'disconnected':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <span className="w-2 h-2 mr-2 rounded-full bg-rose-400"></span>
            Error / Desconectado
          </span>
        )
      case 'checking':
      default:
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <span className="w-2.5 h-2.5 mr-2 border-2 border-t-transparent border-amber-400 rounded-full animate-spin"></span>
            Verificando...
          </span>
        )
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-indigo-500 selection:text-white">
      {/* Top Background Gradients */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute top-10 right-1/4 w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-[100px] pointer-events-none"></div>

      {/* Main Container */}
      <main className="max-w-4xl w-full mx-auto px-6 py-12 flex-grow flex flex-col justify-center relative z-10">
        <header className="mb-10 text-center">
          <div className="inline-block mb-3 px-3 py-1 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 uppercase tracking-widest">
            Fase 01: Arquitectura Base
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-slate-100 via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
            Plataforma Digital Segura
          </h1>
          <p className="mt-2 text-slate-400 text-sm md:text-base">
            Consola técnica de diagnóstico e integridad del sistema
          </p>
        </header>

        {/* Dashboard Card */}
        <section className="bg-slate-900/60 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 md:p-8 shadow-2xl shadow-indigo-950/20">
          <div className="flex items-center justify-between border-b border-slate-800 pb-5 mb-6">
            <div>
              <h2 className="text-xl font-bold text-slate-200">Servicios Clave</h2>
              <p className="text-xs text-slate-500 mt-0.5">Estado actual de la infraestructura del proyecto</p>
            </div>
            <button
              onClick={checkHealth}
              disabled={loading}
              className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50 text-white rounded-lg transition-all shadow-lg shadow-indigo-600/20 active:translate-y-0.5 flex items-center gap-2"
            >
              {loading ? (
                <span className="w-3.5 h-3.5 border-2 border-t-transparent border-white rounded-full animate-spin"></span>
              ) : (
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 4.89M9 11l3 3L22 4"></path>
                </svg>
              )}
              Actualizar
            </button>
          </div>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Frontend Status */}
            <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-5 hover:border-slate-800 transition-all">
              <div className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-2">Frontend Client</div>
              <div className="flex items-center justify-between">
                <span className="text-lg font-semibold text-slate-300">Vite (React + TS)</span>
                {getStatusBadge('active')}
              </div>
            </div>

            {/* Backend Status */}
            <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-5 hover:border-slate-800 transition-all">
              <div className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-2">Backend REST API</div>
              <div className="flex items-center justify-between">
                <span className="text-lg font-semibold text-slate-300">Django (DRF)</span>
                {getStatusBadge(backendStatus)}
              </div>
            </div>

            {/* PostgreSQL Status */}
            <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-5 hover:border-slate-800 transition-all">
              <div className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-2">Base de Datos</div>
              <div className="flex items-center justify-between">
                <span className="text-lg font-semibold text-slate-300">PostgreSQL</span>
                {getStatusBadge(dbStatus)}
              </div>
            </div>

            {/* Redis Status */}
            <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-5 hover:border-slate-800 transition-all">
              <div className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-2">Message Broker</div>
              <div className="flex items-center justify-between">
                <span className="text-lg font-semibold text-slate-300">Redis (Celery)</span>
                {getStatusBadge(redisStatus)}
              </div>
            </div>
          </div>

          {/* Details / Warnings */}
          {errorMsg && (
            <div className="mt-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
              <strong className="block font-bold mb-1">Detalle de error detectado:</strong>
              {errorMsg}
            </div>
          )}

          <div className="mt-6 flex justify-between items-center text-[10px] text-slate-500 border-t border-slate-800/60 pt-4">
            <div>Esquema DB: <span className="text-slate-400">pdg, public</span></div>
            <div>Última verificación: <span className="text-slate-400">{lastChecked || 'Nunca'}</span></div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="w-full text-center py-6 border-t border-slate-900 bg-slate-950/60 text-xs text-slate-600">
        <div>Plataforma Digital Segura &copy; 2026. Todos los derechos reservados.</div>
      </footer>
    </div>
  )
}
