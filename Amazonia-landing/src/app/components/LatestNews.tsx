import React, { useState, useEffect } from 'react';
import { ChevronRight, Loader2 } from 'lucide-react';
import api from '../services/api';

const getFullImageUrl = (path: string | null) => {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const backendHost = import.meta.env.VITE_API_URL 
    ? import.meta.env.VITE_API_URL.replace('/api/v1', '') 
    : 'http://127.0.0.1:8000';
  return `${backendHost}${path}`;
};

const defaultNews = [
  {
    id: 1,
    title: 'Ganó el presidente en Perú',
    description: 'Resultados oficiales confirman la victoria. No se reportan incidencias graves.',
    image: 'https://images.unsplash.com/photo-1580530719806-99398637c403?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwZXJ1JTIwcHJlc2lkZW50JTIwZ292ZXJubWVudHxlbnwxfHx8fDE3ODI0OTE3MzZ8MA&ixlib=rb-4.1.0&q=80&w=400',
    time: '09:30 a.m.'
  },
  {
    id: 2,
    title: 'Terremoto en Bolivia',
    description: 'Sismo de magnitud 6.2 sacude varias zonas del país. No se reportan víctimas fatales.',
    image: 'https://images.unsplash.com/photo-1657069345471-c54f2432b79c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmbG9vZGVkJTIwc3RyZWV0JTIwd2F0ZXJ8ZW58MXx8fHwxNzgyNDkxNzM6fDA&ixlib=rb-4.1.0&q=80&w=400',
    time: '08:15 a.m.'
  },
  {
    id: 3,
    title: 'Lluvias intensas afectan norte',
    description: 'Varias zonas en alerta por desbordes de ríos. Miles en alerta preventiva.',
    image: 'https://images.unsplash.com/photo-1501854140801-50d01698950b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=400',
    time: '07:05 a.m.'
  },
  {
    id: 4,
    title: 'Precio del dólar sigue a la baja',
    description: 'Moneda americana registra ligera caída en el mercado local.',
    image: 'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=400',
    time: '06:30 a.m.'
  },
  {
    id: 5,
    title: 'Selección Peruana se prepara para la fecha',
    description: 'Equipo nacional con miras al próximo desafío de eliminatorias.',
    image: 'https://images.unsplash.com/photo-1622659097509-4d56de14539e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=400',
    time: '05:30 a.m.'
  }
];

const formatCreationTime = (dateStr: string) => {
  try {
    const date = new Date(dateStr);
    let hours = date.getHours();
    const minutes = date.getMinutes();
    const ampm = hours >= 12 ? 'p.m.' : 'a.m.';
    hours = hours % 12;
    hours = hours ? hours : 12; 
    const minutesStr = minutes < 10 ? '0' + minutes : minutes;
    return `${hours}:${minutesStr} ${ampm}`;
  } catch (e) {
    return 'Reciente';
  }
};

const formatCreationDate = (dateStr: string) => {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  } catch (e) {
    return 'Reciente';
  }
};

export function LatestNews() {
  const [newsData, setNewsData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await api.get('/public/news-landing/');
        setNewsData(response.data || []);
      } catch (err) {
        console.warn("Could not fetch landing news, using defaults:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchNews();
  }, []);

  // Limit display to exactly the latest 5 items
  const itemsToDisplay = (newsData.length > 0 ? newsData : defaultNews).slice(0, 5);

  return (
    <div>
      <div className="flex items-center gap-3 mb-6 select-none">
        <div className="w-8 h-8 rounded bg-orange-100 flex items-center justify-center">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ff6600" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
        </div>
        <h2 className="text-2xl font-black text-slate-800">Lo que está pasando</h2>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-10 gap-2">
          <Loader2 className="w-6 h-6 animate-spin text-orange-500" />
          <span className="text-xs text-slate-500 font-bold">Cargando noticias...</span>
        </div>
      ) : (
        <div className="space-y-5">
          {itemsToDisplay.map((item, idx) => (
            <div key={item.id || idx} className="flex gap-3 pb-5 border-b border-gray-200 last:border-0 hover:opacity-95 transition-opacity">
              <img
                src={getFullImageUrl(item.imagen || item.image)}
                alt={item.titulo || item.title}
                className="w-24 h-18 object-cover rounded flex-shrink-0 bg-slate-100 select-none pointer-events-none"
                style={{ height: '72px' }}
              />
              <div className="flex-1 text-left min-w-0">
                <div className="flex items-center gap-1.5 mb-1 select-none font-bold text-xs flex-wrap">
                  <span className="text-orange-600">
                    {item.fecha_actualizacion 
                      ? formatCreationTime(item.fecha_actualizacion) 
                      : item.fecha_creacion 
                      ? formatCreationTime(item.fecha_creacion) 
                      : item.time}
                  </span>
                  <span className="text-slate-300 text-[10px] select-none">•</span>
                  <span className="text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded text-[9px] tracking-wide uppercase font-black">
                    {item.fecha_actualizacion 
                      ? formatCreationDate(item.fecha_actualizacion) 
                      : item.fecha_creacion 
                      ? formatCreationDate(item.fecha_creacion) 
                      : '30 Jun. 2026'}
                  </span>
                </div>
                <h3 className="text-sm font-black mb-1 leading-snug text-slate-800 break-words">
                  {item.titulo || item.title}
                </h3>
                <p className="text-xs text-gray-500 leading-snug font-semibold line-clamp-2 break-all">
                  {item.descripcion || item.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      <button className="mt-4 flex items-center gap-2 text-orange-600 hover:text-orange-700 text-sm font-bold cursor-pointer transition-colors">
        Ver más noticias
        <ChevronRight size={16} />
      </button>
    </div>
  );
}

export default LatestNews;
