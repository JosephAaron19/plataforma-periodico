import React from 'react';
import { Leaf, Monitor, Clock, Lock } from 'lucide-react';
import bgImage from '../../imports/digital_bg.png';

export function DigitalSection() {
  return (
    <div className="relative w-full rounded-2xl overflow-hidden shadow-sm border border-slate-100/50 bg-[#eef6f0] select-none mt-8 min-h-[300px] flex items-center">
      {/* Background Image */}
      <img 
        src={bgImage} 
        alt="Somos tu periódico digital background" 
        className="absolute inset-0 w-full h-full object-cover z-0 pointer-events-none" 
      />
      
      {/* Gradient Overlay for better text readability on small screens */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#eef6f0] via-[#eef6f0]/95 to-transparent md:to-transparent/10 z-5 pointer-events-none" />

      {/* Content Layer */}
      <div className="relative z-10 w-full h-full flex flex-col justify-between p-6 md:p-8 max-w-full md:max-w-[55%] text-left">
        <div>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded bg-[#1a4d2e]/10 flex items-center justify-center">
              <Leaf className="text-[#1a4d2e]" size={20} />
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-[#1a4d2e]">
              Somos tu periódico digital
            </h2>
          </div>
          <p className="text-xs md:text-sm text-[#2d4033] leading-relaxed mb-6 font-semibold max-w-md">
            Llevamos la información veraz y oportuna a donde estés. Lee nuestras ediciones desde cualquier dispositivo.
          </p>
        </div>

        {/* Badges */}
        <div className="flex flex-wrap gap-3 mt-auto">
          <div className="flex items-center gap-2 bg-[#e8f2ea]/90 backdrop-blur-sm rounded-xl p-2 border border-emerald-100/20 shadow-sm">
            <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center flex-shrink-0">
              <Monitor size={16} className="text-[#1a4d2e]" />
            </div>
            <span className="text-[10px] md:text-[11px] font-bold text-[#2d4033] leading-tight max-w-[100px]">
              Accede desde cualquier dispositivo
            </span>
          </div>

          <div className="flex items-center gap-2 bg-[#e8f2ea]/90 backdrop-blur-sm rounded-xl p-2 border border-emerald-100/20 shadow-sm">
            <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center flex-shrink-0">
              <Clock size={16} className="text-[#1a4d2e]" />
            </div>
            <span className="text-[10px] md:text-[11px] font-bold text-[#2d4033] leading-tight max-w-[100px]">
              Ediciones diarias actualizadas
            </span>
          </div>

          <div className="flex items-center gap-2 bg-[#e8f2ea]/90 backdrop-blur-sm rounded-xl p-2 border border-emerald-100/20 shadow-sm">
            <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center flex-shrink-0">
              <Lock size={16} className="text-[#1a4d2e]" />
            </div>
            <span className="text-[10px] md:text-[11px] font-bold text-[#2d4033] leading-tight max-w-[100px]">
              Contenido seguro y confiable
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DigitalSection;
