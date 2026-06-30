import { ChevronLeft, ChevronRight } from 'lucide-react';

const editions = [
  {
    id: 1,
    title: 'Impulsan desarrollo sostenible en la región',
    image: 'https://images.unsplash.com/photo-1564750576234-75de3cc54053?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhbWF6b24lMjByaXZlciUyMGxhbmRzY2FwZXxlbnwxfHx8fDE3ODI0OTE3MzV8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    date: '15 de mayo, 2024',
    edition: 'N° 1258',
    day: '15',
    month: 'MAY'
  },
  {
    id: 2,
    title: 'Proyectos de reforestación avanzan en la zona',
    image: 'https://images.unsplash.com/photo-1599582964755-971498d2b4a0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhbWF6b24lMjByYWluZm9yZXN0JTIwc3Vuc2V0JTIwcml2ZXJ8ZW58MXx8fHwxNzgyNDkxNzM0fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    date: '14 de mayo, 2024',
    edition: 'N° 1257',
    day: '14',
    month: 'MAY'
  },
  {
    id: 3,
    title: 'Celebran el día de la madre en toda la ciudad',
    image: 'https://images.unsplash.com/photo-1612729875065-1385f02852ef?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwZXJ1dmlhbiUyMGxhbmRzY2FwZSUyMG5hdHVyZXxlbnwxfHx8fDE3ODI0OTE3MzV8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    date: '13 de mayo, 2024',
    edition: 'N° 1256',
    day: '13',
    month: 'MAY'
  },
  {
    id: 4,
    title: 'Productores impulsan agricultura orgánica',
    image: 'https://images.unsplash.com/photo-1683476656066-c48bfc06621e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0cm9waWNhbCUyMGZydWl0cyUyMG1hcmtldHxlbnwxfHx8fDE3ODI0OTE3MzZ8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    date: '12 de mayo, 2024',
    edition: 'N° 1255',
    day: '12',
    month: 'MAY'
  },
  {
    id: 5,
    title: 'Jóvenes lideran iniciativas ambientales',
    image: 'https://images.unsplash.com/photo-1622659097509-4d56de14539e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzb2NjZXIlMjB0ZWFtJTIwY2hpbGRyZW58ZW58MXx8fHwxNzgyNDkxNzM3fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    date: '11 de mayo, 2024',
    edition: 'N° 1254',
    day: '11',
    month: 'MAY'
  }
];

export function LatestEditions() {
  return (
    <div>
      <div>
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-orange-100 flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ff6600" strokeWidth="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
            </div>
            <h2 className="text-3xl">Últimas ediciones</h2>
          </div>
          <button className="flex items-center gap-2 text-orange-600 hover:text-orange-700">
            Ver todas
            <ChevronRight size={20} />
          </button>
        </div>

        {/* Navigation */}
        <div className="flex justify-end gap-2 mb-4">
          <button className="w-10 h-10 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-100">
            <ChevronLeft size={20} />
          </button>
          <button className="w-10 h-10 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-100">
            <ChevronRight size={20} />
          </button>
        </div>

        {/* Editions Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {editions.map((edition) => (
            <div key={edition.id} className="bg-white rounded shadow overflow-hidden hover:shadow-md transition-shadow">
              {/* Logo Header */}
              <div className="px-2 py-1.5 border-b flex items-center gap-1">
                <span className="text-xs font-bold" style={{ color: '#ff6600', fontFamily: 'cursive' }}>Amazonía</span>
                <svg width="16" height="16" viewBox="0 0 50 50" fill="none">
                  <circle cx="25" cy="25" r="15" fill="#ff6600"/>
                  <path d="M25 13 L28 20 L25 19 L22 20 Z" fill="#ffcc00"/>
                </svg>
              </div>

              {/* Image */}
              <div className="relative">
                <img
                  src={edition.image}
                  alt={edition.title}
                  className="w-full h-24 object-cover"
                />
                <div className="absolute top-1 left-1 bg-orange-500 text-white px-1.5 py-1 rounded text-center leading-none">
                  <div className="text-sm font-bold">{edition.day}</div>
                  <div className="text-[9px]">{edition.month}</div>
                </div>
              </div>

              {/* Content */}
              <div className="p-2">
                <h3 className="text-[11px] mb-1.5 line-clamp-2 leading-tight">{edition.title}</h3>
                <div className="text-[10px] text-gray-500 mb-2">
                  <p>Edición {edition.edition}</p>
                </div>
                <button className="w-full py-1 border border-gray-300 rounded text-[10px] hover:bg-gray-50">
                  Leer edición
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
