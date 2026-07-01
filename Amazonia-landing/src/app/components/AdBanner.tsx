import React, { useState, useEffect } from 'react';
import { X, ExternalLink } from 'lucide-react';
import adPassgoEvents from '../../imports/ad_passgo_events.jpg';
import adFincontrolSupervision from '../../imports/ad_fincontrol_supervision.jpg';
import adPassgoTickets from '../../imports/ad_passgo_tickets.jpg';
import adFincontrolSmart from '../../imports/ad_fincontrol_smart.jpg';

interface Ad {
  image: string;
  link: string;
  alt: string;
}

const ADS_LIST: Ad[] = [
  {
    image: adPassgoEvents,
    link: "https://passandgo.com.pe",
    alt: "Pass & Go - Ticketing inteligente para eventos"
  },
  {
    image: adFincontrolSupervision,
    link: "https://fincontrol.finatech.com.pe",
    alt: "FinControl - Supervisión inteligente del personal operativo"
  },
  {
    image: adPassgoTickets,
    link: "https://passandgo.com.pe",
    alt: "Pass & Go - Vende entradas y controla accesos"
  },
  {
    image: adFincontrolSmart,
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
    }, 8000); // auto rotates every 8 seconds
    return () => clearInterval(interval);
  }, [autoRotate, positionId]);

  if (!isVisible) return null;

  const currentAd = ADS_LIST[currentIndex];

  return (
    <div className="w-full py-4 select-none px-4 sm:px-6">
      <div className="max-w-7xl mx-auto relative group overflow-hidden rounded-2xl border border-slate-200/60 shadow-lg hover:shadow-xl hover:border-slate-300/80 transition-all duration-300 bg-slate-50">
        
        {/* Label Tag */}
        <span className="absolute top-3 left-3 z-10 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[9px] font-black tracking-widest text-slate-500 uppercase bg-white/90 backdrop-blur-sm border border-slate-200/50 shadow-sm pointer-events-none select-none">
          <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse"></span>
          Anuncio Patrocinado
        </span>

        {/* Close Button */}
        <button
          onClick={() => setIsVisible(false)}
          className="absolute top-3 right-3 z-10 p-1.5 rounded-full bg-slate-900/60 hover:bg-slate-900/80 text-white transition-colors backdrop-blur-sm active:scale-95"
          title="Ocultar anuncio"
        >
          <X className="w-3.5 h-3.5" />
        </button>

        {/* Link Wrapper */}
        <a 
          href={currentAd.link}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full aspect-[4/1] sm:aspect-[5/1] md:aspect-[6/1] overflow-hidden relative cursor-pointer"
        >
          {/* Ad Image with transition */}
          <img
            src={currentAd.image}
            alt={currentAd.alt}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.01]"
          />

          {/* Hover Overlay with CTAs */}
          <div className="absolute inset-0 bg-slate-950/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-end pr-12 pointer-events-none">
            <div className="bg-white/95 backdrop-blur-sm text-slate-800 rounded-full px-4 py-2 text-[10px] font-black tracking-widest uppercase flex items-center gap-1.5 shadow-xl transform translate-x-2 group-hover:translate-x-0 transition-transform duration-300 border border-slate-200/60">
              <span>Visitar Sitio</span>
              <ExternalLink className="w-3 h-3 text-orange-500" />
            </div>
          </div>
        </a>
      </div>
    </div>
  );
}
