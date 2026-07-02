import React, { useState, useEffect } from 'react';
import { X, ExternalLink } from 'lucide-react';

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

interface Ad {
  image: string;
  link: string;
  alt: string;
}

const ADS_LIST: Ad[] = [
  {
    image: "/media/ad_passgo_events.jpg",
    link: "https://passandgo.com.pe",
    alt: "Pass & Go - Ticketing inteligente para eventos"
  },
  {
    image: "/media/ad_fincontrol_supervision.jpg",
    link: "https://fincontrol.finatech.com.pe",
    alt: "FinControl - Supervisión inteligente del personal operativo"
  },
  {
    image: "/media/ad_passgo_tickets.jpg",
    link: "https://passandgo.com.pe",
    alt: "Pass & Go - Vende entradas y controla accesos"
  },
  {
    image: "/media/ad_fincontrol_smart.jpg",
    link: "https://fincontrol.finatech.com.pe",
    alt: "FinControl - Hoy, el control es inteligente"
  }
];

interface AdBannerProps {
  positionId: string;
  initialIndex?: number;
  autoRotate?: boolean;
}

export function AdBanner({ positionId, initialIndex = 0, autoRotate = true }: AdBannerProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex % ADS_LIST.length);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (!autoRotate) return;
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % ADS_LIST.length);
    }, 3500); // rotates every 3.5 seconds
    return () => clearInterval(interval);
  }, [autoRotate, positionId]);

  if (!isVisible) return null;

  const currentAd = ADS_LIST[currentIndex];

  return (
    <div className="w-full py-3 select-none px-4 sm:px-6">
      <div className="max-w-7xl mx-auto relative group overflow-hidden rounded-2xl border border-slate-200/60 shadow-md hover:shadow-lg transition-all duration-300 bg-white">
        
        {/* Label Tag */}
        <span className="absolute top-2.5 left-2.5 z-10 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[8px] font-black tracking-widest text-slate-500 uppercase bg-white/95 backdrop-blur-sm border border-slate-200/50 shadow-sm pointer-events-none select-none">
          <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse"></span>
          Anuncio Patrocinado
        </span>

        {/* Close Button */}
        <button
          onClick={() => setIsVisible(false)}
          className="absolute top-2.5 right-2.5 z-10 p-1.5 rounded-full bg-slate-900/60 hover:bg-slate-900/80 text-white transition-colors backdrop-blur-sm active:scale-95"
          title="Ocultar anuncio"
        >
          <X className="w-3 h-3" />
        </button>

        {/* Link Wrapper */}
        <a 
          href={currentAd.link}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full h-[120px] sm:h-[170px] md:h-[220px] lg:h-[260px] overflow-hidden relative cursor-pointer"
        >
          {/* Ad Image with transition */}
          <img
            src={getFullImageUrl(currentAd.image)}
            alt={currentAd.alt}
            className="w-full h-full block object-cover transition-transform duration-550 group-hover:scale-[1.01]"
          />

          {/* Hover Overlay with CTAs */}
          <div className="absolute inset-0 bg-slate-950/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-end pr-8 pointer-events-none">
            <div className="bg-white/95 backdrop-blur-sm text-slate-800 rounded-full px-3.5 py-1.5 text-[9px] font-black tracking-widest uppercase flex items-center gap-1 shadow-lg transform translate-x-2 group-hover:translate-x-0 transition-transform duration-300 border border-slate-200/60">
              <span>Visitar Sitio</span>
              <ExternalLink className="w-3 h-3 text-orange-500" />
            </div>
          </div>
        </a>
      </div>
    </div>
  );
}
