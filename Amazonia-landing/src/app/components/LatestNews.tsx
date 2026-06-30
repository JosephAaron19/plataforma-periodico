import { ChevronRight } from 'lucide-react';

const news = [
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
    image: 'https://images.unsplash.com/photo-1657069345471-c54f2432b79c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmbG9vZGVkJTIwc3RyZWV0JTIwd2F0ZXJ8ZW58MXx8fHwxNzgyNDkxNzM2fDA&ixlib=rb-4.1.0&q=80&w=400',
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

export function LatestNews() {
  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 rounded bg-orange-100 flex items-center justify-center">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ff6600" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
        </div>
        <h2 className="text-2xl font-semibold">Lo que está pasando</h2>
      </div>

      <div className="space-y-5">
        {news.map((item) => (
          <div key={item.id} className="flex gap-3 pb-5 border-b border-gray-200 last:border-0">
            <img
              src={item.image}
              alt={item.title}
              className="w-24 h-18 object-cover rounded flex-shrink-0"
              style={{ height: '72px' }}
            />
            <div className="flex-1">
              <p className="text-xs text-orange-600 mb-1">{item.time}</p>
              <h3 className="text-sm font-semibold mb-1 leading-snug">{item.title}</h3>
              <p className="text-xs text-gray-500 leading-snug">{item.description}</p>
            </div>
          </div>
        ))}
      </div>

      <button className="mt-4 flex items-center gap-2 text-orange-600 hover:text-orange-700 text-sm">
        Ver más noticias
        <ChevronRight size={16} />
      </button>
    </div>
  );
}
