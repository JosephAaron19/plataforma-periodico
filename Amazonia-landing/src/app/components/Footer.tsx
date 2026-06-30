import { Facebook, Mail } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-12 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          {/* Logo y descripción */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex items-center">
                <h3 className="text-2xl" style={{ color: '#ff6600', fontFamily: 'cursive' }}>
                  Amazonía
                </h3>
                <div className="ml-2">
                  <svg width="40" height="40" viewBox="0 0 50 50" fill="none">
                    <circle cx="25" cy="25" r="20" fill="#ff6600"/>
                    <path d="M25 10 L30 20 L25 18 L20 20 Z" fill="#ffcc00"/>
                    <path d="M25 18 L28 25 L25 23 L22 25 Z" fill="#ffcc00"/>
                  </svg>
                </div>
              </div>
              <h3 className="text-2xl" style={{ color: '#ff6600', fontFamily: 'cursive' }}>
                Diario
              </h3>
            </div>
            <p className="text-gray-400 text-sm mb-4">
              La información que conecta nuestra región. Noticias locales, nacionales e internacionales con el enfoque que importa a nuestra comunidad.
            </p>
            <div className="flex gap-3">
              <a href="#" className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center hover:bg-gray-700">
                <Facebook size={20} />
              </a>
              <a href="#" className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center hover:bg-gray-700">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                </svg>
              </a>
              <a href="#" className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center hover:bg-gray-700">
                <Mail size={20} />
              </a>
            </div>
          </div>

          {/* Enlaces */}
          <div>
            <h4 className="mb-4">Secciones</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><a href="#" className="hover:text-white">Locales</a></li>
              <li><a href="#" className="hover:text-white">Regionales</a></li>
              <li><a href="#" className="hover:text-white">Nacionales</a></li>
              <li><a href="#" className="hover:text-white">Internacionales</a></li>
              <li><a href="#" className="hover:text-white">Deportes</a></li>
            </ul>
          </div>

          {/* Contacto */}
          <div>
            <h4 className="mb-4">Contacto</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><a href="#" className="hover:text-white">Acerca de nosotros</a></li>
              <li><a href="#" className="hover:text-white">Anúnciate con nosotros</a></li>
              <li><a href="#" className="hover:text-white">Términos y condiciones</a></li>
              <li><a href="#" className="hover:text-white">Política de privacidad</a></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-8 text-center text-sm text-gray-400">
          <p>&copy; 2026 Amazonía Diario. Todos los derechos reservados.</p>
        </div>
      </div>
    </footer>
  );
}
