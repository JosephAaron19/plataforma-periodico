import React, { useState, useEffect } from 'react';
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

export function HeroSection() {
  const [config, setConfig] = useState({
    hero_title: 'La información que conecta nuestra región',
    hero_subtitle: 'Noticias locales, nacionales e internacionales con el enfoque que importa a nuestra comunidad.',
    hero_background_url: 'https://images.unsplash.com/photo-1599582964755-971498d2b4a0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhbWF6b24lMjByYWluZm9yZXN0JTIwc3Vuc2V0JTIwcml2ZXJ8ZW58MXx8fHwxNzgyNDkxNzM0fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral',
    hero_background_position: 'center'
  });

  useEffect(() => {
    const fetchHeroConfig = async () => {
      try {
        const response = await api.get('/configuration/landing/');
        if (response.data) {
          setConfig(response.data);
        }
      } catch (err) {
        console.warn("Could not fetch hero landing configuration, using defaults:", err);
      }
    };
    fetchHeroConfig();
  }, []);

  // Split title into parts to colorize "conecta nuestra región" or automatically colorize second half of long phrases
  const renderTitle = (title: string) => {
    const targetPhrase = "conecta nuestra región";
    const index = title.toLowerCase().indexOf(targetPhrase.toLowerCase());
    
    if (index !== -1) {
      const before = title.substring(0, index);
      const matched = title.substring(index, index + targetPhrase.length);
      const after = title.substring(index + targetPhrase.length);
      return (
        <>
          {before}
          <span className="text-[#ea580c]">{matched}</span>
          {after}
        </>
      );
    }

    // Auto-colorize second half if the phrase is long
    const words = title.split(/\s+/);
    if (words.length > 3) {
      const mid = Math.ceil(words.length / 2);
      const firstPart = words.slice(0, mid).join(' ');
      const secondPart = words.slice(mid).join(' ');
      return (
        <>
          {firstPart}{' '}
          <span className="text-[#ea580c]">{secondPart}</span>
        </>
      );
    }
    
    return title;
  };

  const getPositionClass = (pos: string) => {
    if (pos === 'top') return 'object-top';
    if (pos === 'bottom') return 'object-bottom';
    return 'object-center';
  };

  const bgImgUrl = getFullImageUrl(config.hero_background_url);

  return (
    <section className="relative min-h-[600px] flex items-center overflow-hidden">
      {/* Background Image Container */}
      <div className="absolute inset-0 z-0 bg-slate-950 overflow-hidden">
        {/* Background image covering 100% of the section without empty gaps, positioned vertically based on config */}
        <img 
          src={bgImgUrl}
          alt="Amazonía landscape"
          className={`w-full h-full object-cover ${getPositionClass(config.hero_background_position)} select-none pointer-events-none`}
        />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 py-16 grid md:grid-cols-2 gap-8 items-center">
        {/* Left Content */}
        <div className="text-white text-center md:text-left select-none">
          <h1 className="text-3xl sm:text-4xl md:text-5xl mb-4 font-black leading-[1.15] drop-shadow-md">
            {renderTitle(config.hero_title)}
          </h1>
          <p className="text-base sm:text-lg mb-8 text-gray-200 font-semibold max-w-xl leading-relaxed whitespace-pre-line drop-shadow-sm">
            {config.hero_subtitle}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center md:justify-start">
            <button className="px-6 py-3 text-white rounded flex items-center justify-center gap-2 font-bold cursor-pointer transition-colors hover:bg-[#153e25] shadow-sm active:scale-[0.98]" style={{ backgroundColor: '#1a4d2e' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="9" y1="3" x2="9" y2="21"/>
              </svg>
              Leer edición digital
            </button>
            <button 
              onClick={() => {
                document.getElementById('planes')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="px-6 py-3 bg-white text-gray-800 rounded hover:bg-gray-100 font-bold transition-all cursor-pointer shadow-sm active:scale-[0.98]"
            >
              Conoce nuestros planes
            </button>
          </div>
        </div>

        {/* Right Content - Newspaper Preview (Static as requested) */}
        <div className="bg-white rounded-lg shadow-2xl p-6 max-w-md mx-auto md:ml-auto w-full z-10">
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
            <div className="ml-auto text-right">
              <p className="text-xs text-gray-500 font-medium">Edición N° 1258</p>
              <p className="text-xs text-gray-500 font-medium">Viernes, 15 de mayo, 2026</p>
            </div>
          </div>
          <div className="border-t-4 border-orange-500 pt-4">
            <h2 className="text-xl mb-3 text-left font-black" style={{ color: '#1a4d2e' }}>
              Impulsan desarrollo sostenible en la región amazónica
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-left">
                <h4 className="text-xs mb-2 font-bold truncate">Comunidades nativas impulsan ecoturismo</h4>
                <img 
                  src="https://images.unsplash.com/photo-1612729875065-1385f02852ef?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwZXJ1dmlhbiUyMGxhbmRzY2FwZSUyMG5hdHVyZXxlbnwxfHx8fDE3ODI0OTE3MzV8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
                  alt="Comunidades"
                  className="w-full h-20 object-cover rounded"
                />
                <p className="text-[10px] text-gray-500 mt-1 leading-tight font-semibold">Familias participan en proyectos de turismo rural</p>
              </div>
              <div className="text-left">
                <h4 className="text-xs mb-2 font-bold truncate">Turismo en la Amazonía crece y beneficia a miles</h4>
                <img 
                  src="https://images.unsplash.com/photo-1564750576234-75de3cc54053?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhbWF6b24lMjByaXZlciUyMGxhbmRzY2FwZXxlbnwxfHx8fDE3ODI0OTE3MzV8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
                  alt="Turismo"
                  className="w-full h-20 object-cover rounded"
                />
                <p className="text-[10px] text-gray-500 mt-1 leading-tight font-semibold">Millones de turistas visitan zonas rurales</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default HeroSection;
