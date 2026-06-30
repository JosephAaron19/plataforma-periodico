import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Newspaper, BookOpen, Users, CreditCard, Clock, Check, Shield, 
  Bookmark, Lock, ChevronLeft, ChevronRight, Sparkles, Layers, 
  Activity, Share2, Key
} from 'lucide-react';
import { useSimulation } from '../../contexts/SimulationContext';

const Landing: React.FC = () => {
  const { customImage, setCustomImage } = useSimulation();

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setCustomImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCustomImage(e.target.value || null);
  };

  const handleResetImage = () => {
    setCustomImage(null);
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 text-slate-800 font-sans selection:bg-brand-500/30 overflow-x-hidden">
      
      {/* Hero Section - 3 Columns Layout (Light modern background) */}
      <section className="relative min-h-[85vh] flex items-center pt-10 pb-16 lg:pt-14 lg:pb-24 overflow-hidden bg-gradient-to-br from-slate-100 via-slate-50 to-white">
        {/* Glow Effects */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
          <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] bg-brand-500/10 rounded-full blur-[120px] opacity-35"></div>
          <div className="absolute bottom-[20%] right-[-10%] w-[45vw] h-[45vw] bg-blue-500/5 rounded-full blur-[120px] opacity-25"></div>
        </div>

        <div className="w-full max-w-[90rem] mx-auto px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
            
            {/* Column 1 (Left): Info & CTAs */}
            <div className="lg:col-span-4 flex flex-col items-start text-left relative z-20 space-y-6">
              <div className="inline-flex items-center space-x-2 border border-brand-500/30 rounded-full px-3.5 py-1.5 bg-brand-50/80 backdrop-blur-sm">
                <BookOpen className="w-3.5 h-3.5 text-brand-600" />
                <span className="text-[10px] lg:text-[11px] font-bold tracking-widest text-brand-700 uppercase">
                  Digitalización y Monetización de Prensa
                </span>
              </div>
              
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-slate-900 tracking-tight leading-[1.15]">
                Convierte tus PDFs en <span className="text-brand-600 bg-gradient-to-r from-brand-600 to-emerald-600 bg-clip-text text-transparent">periódicos digitales</span> y monetiza cada edición
              </h1>
              
              <p className="text-sm lg:text-base text-slate-600 leading-relaxed max-w-[95%]">
                Accede a ediciones completas, contenido exclusivo y mantente informado con la mejor experiencia de lectura digital.
              </p>

              {/* Benefits list in row */}
              <div className="flex flex-row flex-wrap gap-x-4 gap-y-2 text-[11px] font-bold text-slate-700 w-full pt-1">
                <div className="flex items-center bg-white/60 px-3 py-1 rounded-full border border-slate-100 shadow-sm">
                  <span className="w-2 h-2 rounded-full bg-brand-500 mr-2"></span>
                  Compra segura
                </div>
                <div className="flex items-center bg-white/60 px-3 py-1 rounded-full border border-slate-100 shadow-sm">
                  <span className="w-2 h-2 rounded-full bg-brand-500 mr-2"></span>
                  Acceso inmediato
                </div>
                <div className="flex items-center bg-white/60 px-3 py-1 rounded-full border border-slate-100 shadow-sm">
                  <span className="w-2 h-2 rounded-full bg-brand-500 mr-2"></span>
                  Disponible 24/7
                </div>
              </div>
              
              {/* CTAs */}
              <div className="flex flex-col sm:flex-row gap-3 w-full max-w-[440px] pt-2">
                <Link to="/catalog" className="flex-1 inline-flex items-center justify-center px-6 py-3.5 text-sm font-bold text-dark-900 bg-brand-500 hover:bg-brand-400 rounded-xl transition-all shadow-lg shadow-brand-500/20 text-center hover:scale-[1.02] duration-200">
                  Explorar periódicos
                </Link>
                <a href="#precios" className="flex-1 inline-flex items-center justify-center px-6 py-3.5 text-sm font-bold text-white bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-xl transition-all shadow-md shadow-black/10 text-center hover:scale-[1.02] duration-200">
                  Ver planes de suscripción
                </a>
              </div>

              {/* Social Proof */}
              <div className="flex items-center gap-4 border-t border-slate-200/60 pt-5 w-full mt-2">
                <div className="flex -space-x-2">
                  {[1, 2, 3, 4].map((i) => (
                    <img key={i} className="w-7 h-7 rounded-full border-2 border-white bg-slate-200" src={`https://i.pravatar.cc/100?img=${i+12}`} alt={`Lector ${i}`} />
                  ))}
                </div>
                <div className="text-[12px] text-slate-500 leading-snug">
                  <span className="text-slate-800 font-bold block">+10,000 lectores</span>
                  ya disfrutan de DigitalSaaS
                </div>
              </div>

              {/* Simulation Uploader */}
              <div className="w-full max-w-[440px] bg-white border border-slate-100 p-4 rounded-2xl shadow-sm space-y-3 mt-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-[11px] font-bold text-slate-700 flex items-center gap-1.5 uppercase tracking-wider">
                    <Sparkles className="w-3.5 h-3.5 text-brand-600" /> Simulación de Portada
                  </h3>
                  {customImage && (
                    <button 
                      onClick={handleResetImage}
                      className="text-[10px] text-red-500 hover:text-red-600 font-bold transition-colors"
                    >
                      Restablecer
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <div className="flex flex-col justify-center p-2 bg-slate-50 border border-slate-100 rounded-lg">
                    <label className="text-[8px] font-bold text-slate-500 uppercase tracking-wider mb-1 block">
                      Subir imagen local
                    </label>
                    <input 
                      type="file" 
                      accept="image/*" 
                      onChange={handleImageUpload}
                      className="block w-full text-[9px] text-slate-500 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-[9px] file:font-semibold file:bg-brand-500/10 file:text-brand-700 hover:file:bg-brand-500/20 cursor-pointer"
                    />
                  </div>
                  <div className="flex flex-col justify-center p-2 bg-slate-50 border border-slate-100 rounded-lg">
                    <label className="text-[8px] font-bold text-slate-500 uppercase tracking-wider mb-1 block">
                      Pegar URL de imagen
                    </label>
                    <input 
                      type="text" 
                      placeholder="https://url/portada.jpg" 
                      onChange={handleUrlChange}
                      className="w-full bg-white border border-slate-200 rounded px-2 py-1 text-[9px] text-slate-700 placeholder-slate-400 focus:outline-none focus:border-brand-500 font-medium"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Column 2 (Center): Newspaper Laptop/Tablet Mockup */}
            <div className="lg:col-span-5 flex justify-center items-center relative">
              {/* Background soft shadow glow */}
              <div className="absolute -inset-4 bg-brand-500/5 rounded-3xl blur-3xl opacity-70 pointer-events-none"></div>

              {/* Large Desktop/Browser Mockup */}
              <div className="w-full aspect-[4/3] bg-white rounded-2xl shadow-xl border border-slate-200/80 overflow-hidden flex flex-col transition-all duration-300 hover:scale-[1.01] relative z-10">
                
                {/* Browser Header */}
                <div className="h-9 bg-slate-100 border-b border-slate-200 flex items-center px-4 gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-400"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-400"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-green-400"></div>
                  <div className="ml-4 text-[10px] text-slate-400 font-mono select-none bg-white px-3 py-0.5 rounded border border-slate-200 truncate max-w-[240px]">
                    reader.digitalsaas.com/la-voz-del-sur
                  </div>
                </div>

                {/* Browser Viewport */}
                <div className="flex flex-1 overflow-hidden">
                  
                  {/* Mockup Mini-Sidebar */}
                  <div className="w-11 bg-slate-50 border-r border-slate-150 flex flex-col items-center py-4 gap-4 flex-shrink-0">
                    <div className="w-7 h-7 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-700">
                      <Newspaper className="w-3.5 h-3.5" />
                    </div>
                    <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                    <Bookmark className="w-3.5 h-3.5 text-slate-400" />
                    <Users className="w-3.5 h-3.5 text-slate-400" />
                  </div>

                  {/* Mockup Main page content */}
                  <div className="flex-1 bg-white p-4 overflow-hidden flex flex-col">
                    {customImage ? (
                      <div className="w-full h-full flex items-center justify-center overflow-hidden bg-slate-50 rounded-lg">
                        <img src={customImage} className="w-full h-full object-contain" alt="Portada" />
                      </div>
                    ) : (
                      <>
                        {/* Newspaper Banner */}
                        <div className="border-b-2 border-slate-900 pb-2 mb-3 flex justify-between items-end flex-shrink-0">
                          <div>
                            <h2 className="text-xl font-serif font-black text-slate-950 tracking-tight leading-none text-left">
                              LA VOZ DEL SUR
                            </h2>
                            <div className="flex gap-2 text-[5px] text-slate-400 uppercase tracking-widest font-bold mt-1.5">
                              <span>Portada</span> <span>LOCALES</span> <span>Política</span> <span>Economía</span>
                            </div>
                          </div>
                          <div className="text-right text-[7px] text-slate-500 leading-none">
                            <div className="font-bold">Edición #120</div>
                            <div className="mt-0.5">15 Mayo 2026</div>
                          </div>
                        </div>

                        {/* Articles Grid */}
                        <div className="grid grid-cols-12 gap-3 overflow-hidden flex-1 text-left">
                          <div className="col-span-8 flex flex-col gap-2">
                            <span className="text-[5px] font-bold text-red-600 tracking-widest uppercase">NACIONAL</span>
                            <h3 className="text-[11px] font-serif font-bold text-slate-900 leading-snug">
                              Economía local muestra crecimiento del 2.8% en el primer trimestre
                            </h3>
                            <p className="text-[5px] text-slate-500 leading-relaxed">
                              El informe del BCP destaca el dinamismo de diversos sectores económicos en la región sur del país...
                            </p>
                            <div className="w-full h-24 bg-gradient-to-tr from-slate-100 to-slate-200 rounded-md overflow-hidden relative border border-slate-200 flex items-center justify-center">
                              <Newspaper className="w-6 h-6 text-slate-300" />
                            </div>
                          </div>
                          
                          <div className="col-span-4 flex flex-col gap-2.5 divide-y divide-slate-100">
                            <div className="pb-1.5">
                              <span className="text-[4.5px] font-bold text-brand-600 tracking-widest uppercase block mb-0.5">DEPORTES</span>
                              <h4 className="text-[7.5px] font-bold text-slate-900 leading-snug">Equipo local clasifica a la final del torneo</h4>
                              <div className="w-full h-9 bg-slate-100 rounded mt-1.5 border border-slate-150"></div>
                            </div>
                            <div className="pt-1.5">
                              <span className="text-[4.5px] font-bold text-purple-600 tracking-widest uppercase block mb-0.5">CULTURA</span>
                              <h4 className="text-[7.5px] font-bold text-slate-900 leading-snug">Festival de arte reúne a miles en Arequipa</h4>
                            </div>
                          </div>
                        </div>

                        {/* Page Footer */}
                        <div className="border-t border-slate-100 pt-2 mt-2 flex justify-between items-center text-[7px] text-slate-400 flex-shrink-0">
                          <span>Índice de Páginas • Pág. 1 / 32</span>
                          <div className="flex gap-1">
                            <ChevronLeft className="w-2.5 h-2.5 text-slate-300" />
                            <ChevronRight className="w-2.5 h-2.5 text-slate-500" />
                          </div>
                        </div>
                      </>
                    )}
                  </div>

                </div>

              </div>
            </div>

            {/* Column 3 (Right): Smartphone Mockup (Premium Access highlighted) */}
            <div className="lg:col-span-3 flex justify-center items-center relative">
              <div className="relative group w-[180px] lg:w-[190px] aspect-[9/19] bg-slate-900 border-[5px] border-slate-800 rounded-[2.5rem] shadow-xl overflow-hidden flex flex-col flex-shrink-0 transition-transform duration-300 hover:-translate-y-1 z-20">
                
                {/* Notch */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-24 h-4 bg-slate-800 rounded-b-xl z-40 flex items-center justify-center">
                  <div className="w-10 h-1 bg-black rounded-full mb-1"></div>
                </div>
                
                {/* Phone screen content */}
                <div className="flex-1 p-2.5 pt-6 flex flex-col relative bg-slate-950 z-10 justify-between">
                  <div>
                    {/* Header */}
                    <div className="text-center font-serif font-black text-[9px] text-white tracking-wider border-b border-white/5 pb-1 mb-2">
                      LA VOZ DEL SUR
                    </div>
                    
                    {/* Preview Cover */}
                    {customImage ? (
                      <div className="bg-white p-1 rounded-lg shadow flex-1 aspect-[3/4] overflow-hidden flex items-center justify-center mb-2">
                        <img src={customImage} className="w-full h-full object-contain" alt="Portada" />
                      </div>
                    ) : (
                      <div className="bg-white p-2 rounded-lg shadow flex flex-col aspect-[3/4] overflow-hidden mb-2 text-left">
                        <div className="text-center border-b border-slate-900 pb-0.5 mb-1.5">
                          <span className="font-serif font-bold text-[8px] text-slate-950 block">LA VOZ DEL SUR</span>
                          <span className="text-[3px] text-slate-400">Edición #120 • Premium</span>
                        </div>
                        <div className="flex-1 bg-slate-50 flex flex-col gap-1 p-1">
                          <div className="h-6 bg-slate-800 rounded-sm"></div>
                          <div className="h-0.5 bg-slate-300 w-full"></div>
                          <div className="h-0.5 bg-slate-300 w-4/5"></div>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Premium Checkout Banner */}
                  <div className="bg-slate-900/95 border border-white/10 rounded-xl p-3 shadow-2xl flex flex-col mt-auto">
                    <div className="inline-flex items-center gap-1 mb-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      <span className="text-[6.5px] text-slate-300 font-bold uppercase tracking-wider">Acceso Premium Completo</span>
                    </div>
                    
                    <span className="text-sm font-extrabold text-white block mb-2">US$ 2.50</span>
                    
                    <button className="w-full bg-brand-500 hover:bg-brand-400 text-dark-900 font-extrabold text-[8.5px] py-2 rounded-lg transition-all uppercase tracking-wider mb-2 shadow-md shadow-brand-500/10">
                      Comprar acceso
                    </button>
                    
                    <div className="flex items-center justify-between text-[5.5px] text-slate-400">
                      <div className="flex items-center gap-0.5">
                        <Lock className="w-1.5 h-1.5 text-emerald-400" />
                        <span>Pago 100% Seguro</span>
                      </div>
                      <span className="text-[5.5px] text-slate-400 font-bold bg-white/10 px-1 rounded">VISA / MC</span>
                    </div>
                  </div>

                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Floating Metrics Section (Light, elegant, floating below mockups) */}
      <section className="relative z-30 -mt-10 mb-16 max-w-5xl mx-auto w-full px-6">
        <div className="bg-white/90 backdrop-blur-md border border-slate-200/60 rounded-2xl py-5 px-6 shadow-lg">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center divide-x divide-slate-100">
            
            {/* Metric 1 */}
            <div className="flex items-center gap-3 justify-center">
              <div className="w-10 h-10 rounded-full bg-brand-500/10 flex items-center justify-center text-brand-600 flex-shrink-0">
                <BookOpen className="w-4.5 h-4.5" />
              </div>
              <div className="text-left">
                <div className="text-lg md:text-xl font-black text-slate-900 leading-none">+2.5K</div>
                <div className="text-[10px] font-semibold text-slate-500 mt-1 uppercase tracking-wider">Ediciones publicadas</div>
              </div>
            </div>

            {/* Metric 2 */}
            <div className="flex items-center gap-3 justify-center pl-4 md:pl-0">
              <div className="w-10 h-10 rounded-full bg-brand-500/10 flex items-center justify-center text-brand-600 flex-shrink-0">
                <Users className="w-4.5 h-4.5" />
              </div>
              <div className="text-left">
                <div className="text-lg md:text-xl font-black text-slate-900 leading-none">+120K</div>
                <div className="text-[10px] font-semibold text-slate-500 mt-1 uppercase tracking-wider">Lectores activos</div>
              </div>
            </div>

            {/* Metric 3 */}
            <div className="flex items-center gap-3 justify-center pl-4 md:pl-0">
              <div className="w-10 h-10 rounded-full bg-brand-500/10 flex items-center justify-center text-brand-600 flex-shrink-0">
                <CreditCard className="w-4.5 h-4.5" />
              </div>
              <div className="text-left">
                <div className="text-lg md:text-xl font-black text-slate-900 leading-none">+85K</div>
                <div className="text-[10px] font-semibold text-slate-500 mt-1 uppercase tracking-wider">Accesos vendidos</div>
              </div>
            </div>

            {/* Metric 4 */}
            <div className="flex items-center gap-3 justify-center pl-4 md:pl-0">
              <div className="w-10 h-10 rounded-full bg-brand-500/10 flex items-center justify-center text-brand-600 flex-shrink-0">
                <Clock className="w-4.5 h-4.5" />
              </div>
              <div className="text-left">
                <div className="text-lg md:text-xl font-black text-slate-900 leading-none">99.9%</div>
                <div className="text-[10px] font-semibold text-slate-500 mt-1 uppercase tracking-wider">Uptime</div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Catalog List Section */}
      <section className="py-16 bg-white border-t border-slate-100">
        <div className="max-w-7xl mx-auto px-6">
          
          {/* Header & Filter options */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 mb-10">
            <div className="text-left">
              <h2 className="text-2xl font-black tracking-tight text-slate-900">
                Periódicos disponibles
              </h2>
              <p className="mt-1.5 text-xs text-slate-500 font-medium">
                Explora las portadas de los periódicos que confían en nosotros
              </p>
            </div>
            <div className="flex flex-row items-center gap-2">
              <span className="text-xs text-slate-400 font-bold mr-1">Filtrar por:</span>
              <button className="px-3 py-1.5 text-xs font-bold bg-brand-500 text-dark-900 rounded-lg shadow-sm border border-brand-400">Todas</button>
              <button className="px-3 py-1.5 text-xs font-bold bg-slate-50 text-slate-700 rounded-lg hover:bg-slate-100 transition-colors border border-slate-200">Nacionales</button>
              <button className="px-3 py-1.5 text-xs font-bold bg-slate-50 text-slate-700 rounded-lg hover:bg-slate-100 transition-colors border border-slate-200">Locales</button>
            </div>
          </div>

          {/* Catalog grid matching style */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
            {[
              { id: '125', name: 'La Voz del Sur', date: 'Arequipa, 15 Mayo 2026', price: 'US$ 2.50', cardColor: 'bg-[#ffc107]', textLogo: 'LA VOZ DEL SUR', textColor: 'text-slate-900' },
              { id: '842', name: 'El Pueblo', date: 'Mayo 2026 • Plan mensual', price: 'US$ 2.00', cardColor: 'bg-[#003882]', textLogo: 'El Pueblo', textColor: 'text-white' },
              { id: '310', name: 'Correo Arequipa', date: 'Arequipa, 14 Mayo 2026', price: 'US$ 2.00', cardColor: 'bg-[#d90429]', textLogo: 'Correo', textColor: 'text-white' },
              { id: '038', name: 'Diario Opinión', date: 'Abril 2026 • Plan mensual', price: 'US$ 2.50', cardColor: 'bg-[#0d1e38]', textLogo: 'Diario Opinión', textColor: 'text-white' },
              { id: '210', name: 'Gestión', date: 'Lima, 13 Mayo 2026', price: 'US$ 2.00', cardColor: 'bg-[#830a1c]', textLogo: 'GESTIÓN', textColor: 'text-white' }
            ].map((mag, i) => (
              <Link 
                key={i} 
                to={`/editions/${mag.id}`} 
                className="group flex flex-col bg-white border border-slate-200 rounded-2xl overflow-hidden hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
              >
                
                {/* Visual Cover card mockup matching the mockup image */}
                <div className="aspect-[3/4] bg-slate-50 relative overflow-hidden flex items-center justify-center p-3.5 border-b border-slate-200">
                  <div className="w-full h-full bg-white shadow-sm rounded-lg flex flex-col p-2.5 transform group-hover:scale-[1.01] transition-transform duration-300 overflow-hidden relative">
                    
                    {mag.id === '125' && customImage ? (
                      <div className="w-full h-full flex items-center justify-center overflow-hidden">
                        <img src={customImage} className="w-full h-full object-contain" alt="Portada" />
                      </div>
                    ) : (
                      <>
                        {/* Custom Colored Banner for specific brand mockup */}
                        <div className={`w-full py-1 text-center text-[8px] font-serif font-black tracking-tight mb-2 flex-shrink-0 ${mag.cardColor} ${mag.textColor || 'text-white'} rounded-md flex items-center justify-center min-h-[22px] px-1`}>
                          <span className="truncate">{mag.textLogo}</span>
                        </div>
                        
                        {/* Newspaper Content blocks */}
                        <div className="flex-1 flex flex-col gap-1.5 overflow-hidden text-left">
                          <div className="h-0.5 bg-slate-900 w-full mb-0.5"></div>
                          <div className="h-1 bg-slate-200 w-full"></div>
                          <div className="h-1 bg-slate-200 w-3/4"></div>
                          <div className="h-12 bg-slate-50 rounded border border-slate-200 mt-1 flex items-center justify-center">
                            <Newspaper className="w-4 h-4 text-slate-300 opacity-60" />
                          </div>
                        </div>

                        {/* Tiny Indicator badge */}
                        <div className="mt-2 text-[5.5px] font-bold text-brand-700 bg-brand-50 border border-brand-200/40 rounded px-1 py-0.5 w-fit uppercase flex-shrink-0">
                          Edición del día
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Card footer details */}
                <div className="p-4 flex flex-col items-start flex-1 w-full text-left">
                  <h3 className="font-bold text-slate-800 text-xs mb-1 truncate w-full group-hover:text-brand-600 transition-colors">{mag.name}</h3>
                  <p className="text-[10px] text-slate-500 mb-3 font-bold">{mag.date}</p>
                  
                  <div className="mt-auto w-full py-2 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-lg group-hover:bg-brand-500 group-hover:text-dark-900 group-hover:border-brand-400 transition-all text-center">
                    Ver edición
                  </div>
                </div>

              </Link>
            ))}
          </div>

        </div>
      </section>

      {/* How it Works Section */}
      <section id="como-funciona" className="py-20 bg-slate-100 text-slate-800 border-t border-slate-200/50">
        <div className="max-w-7xl mx-auto px-6">
          
          <div className="text-center max-w-xl mx-auto mb-16">
            <span className="text-xs font-bold text-brand-700 uppercase tracking-widest">¿Cómo funciona?</span>
            <h2 className="text-3xl font-black text-slate-900 mt-2 mb-3">
              Crea tu periódico digital en 4 simples pasos
            </h2>
            <p className="text-xs text-slate-500 font-semibold leading-relaxed">
              Te acompañamos en todo el proceso para digitalizar tus ediciones en minutos
            </p>
          </div>

          {/* 4 Steps grid with connecting indicators */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 relative">
            
            {/* Step 1 */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200/50 flex flex-col items-center text-center relative group hover:shadow-md transition-all">
              <div className="w-10 h-10 rounded-full bg-brand-500 text-dark-900 flex items-center justify-center font-bold text-sm mb-4">
                1
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-2">Subes tu PDF</h3>
              <p className="text-xs text-slate-500 leading-relaxed font-semibold">
                Arrastra tu documento original directamente al panel administrativo en un clic.
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200/50 flex flex-col items-center text-center relative group hover:shadow-md transition-all">
              <div className="w-10 h-10 rounded-full bg-brand-500 text-dark-900 flex items-center justify-center font-bold text-sm mb-4">
                2
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-2">Procesamiento digital</h3>
              <p className="text-xs text-slate-500 leading-relaxed font-semibold">
                Convertimos las páginas de tu archivo PDF en imágenes adaptables de alta definición.
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200/50 flex flex-col items-center text-center relative group hover:shadow-md transition-all">
              <div className="w-10 h-10 rounded-full bg-brand-500 text-dark-900 flex items-center justify-center font-bold text-sm mb-4">
                3
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-2">Defines el acceso</h3>
              <p className="text-xs text-slate-500 leading-relaxed font-semibold">
                Elige si el contenido será libre o establece un precio de venta para tus ediciones.
              </p>
            </div>

            {/* Step 4 */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200/50 flex flex-col items-center text-center relative group hover:shadow-md transition-all">
              <div className="w-10 h-10 rounded-full bg-brand-500 text-dark-900 flex items-center justify-center font-bold text-sm mb-4">
                4
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-2">Recibes ingresos</h3>
              <p className="text-xs text-slate-500 leading-relaxed font-semibold">
                Monetiza con tu contenido y recibe tus pagos de forma directa y simplificada.
              </p>
            </div>

          </div>

        </div>
      </section>

      {/* Demo + Subscription Plans Section */}
      <section id="precios" className="py-20 bg-white text-slate-800 border-t border-slate-100">
        <div className="max-w-7xl mx-auto px-6">
          
          <div className="grid lg:grid-cols-12 gap-12 items-start">
            
            {/* Demo Column (Left) */}
            <div id="demo" className="lg:col-span-5 flex flex-col h-full bg-slate-50 p-6 rounded-2xl border border-slate-200/60 shadow-sm justify-between min-h-[460px] text-left">
              <div>
                <h2 className="text-2xl font-black text-slate-900 mb-1">Prueba la lectura digital</h2>
                <p className="text-xs text-slate-500 mb-6 font-semibold">Experimenta cómo se visualizan las portadas de manera interactiva.</p>
                
                {/* Mock Viewport */}
                <div className="relative bg-[#0d111a] rounded-xl border border-slate-200 p-2 flex flex-col overflow-hidden mb-6 aspect-[16/10] justify-between shadow-inner">
                  <div className="h-5 bg-[#121824] flex items-center px-2 gap-1 rounded-t-md mb-2">
                     <div className="w-1.5 h-1.5 rounded-full bg-red-500"></div>
                     <div className="w-1.5 h-1.5 rounded-full bg-yellow-500"></div>
                     <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
                  </div>
                  <div className="flex-1 bg-white rounded-md flex flex-col p-2.5 overflow-hidden">
                    <div className="border-b border-gray-200 pb-1 mb-2 text-center">
                      <span className="font-serif font-bold text-[10px] text-gray-900 block">LA VOZ DEL SUR</span>
                      <span className="text-[3.5px] text-gray-400">Edición #120 • 15 Mayo 2026</span>
                    </div>
                    <div className="flex-1 bg-slate-50 rounded flex flex-col p-1.5 gap-1">
                      <div className="h-8 bg-slate-900 rounded-sm"></div>
                      <div className="h-1 bg-gray-300 w-full"></div>
                      <div className="h-1 bg-gray-300 w-4/5"></div>
                    </div>
                  </div>
                </div>
              </div>
              
              <Link to="/editions/125" className="w-full bg-brand-500 hover:bg-brand-400 text-dark-900 font-bold py-3.5 rounded-xl transition-all flex items-center justify-center gap-2 text-sm shadow-md shadow-brand-500/10 text-center hover:scale-[1.01]">
                Ver demostración en vivo (La Voz del Sur)
              </Link>
            </div>

            {/* Plans Card (Right) */}
            <div className="lg:col-span-7 flex flex-col h-full justify-between text-left">
              <div className="mb-6">
                <h2 className="text-2xl font-black text-slate-900 mb-1">Elige el plan ideal para tu negocio</h2>
                <p className="text-xs text-slate-500 font-semibold">Configura y publica tus ediciones bajo el esquema perfecto.</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                
                {/* Básico */}
                <div className="bg-white border border-slate-200 rounded-2xl p-5 flex flex-col justify-between hover:shadow-md transition-shadow">
                  <div>
                    <h3 className="font-bold text-slate-900 text-base mb-0.5">Básico</h3>
                    <p className="text-[10px] text-slate-400 mb-4 font-semibold">Lectura y pruebas iniciales</p>
                    <div className="flex items-baseline mb-4">
                      <span className="text-2xl font-black text-slate-950">US$ 0</span>
                      <span className="text-xs text-slate-400 ml-1">/mes</span>
                    </div>
                    
                    <ul className="space-y-2.5 mb-6 text-[10px] text-slate-600 font-semibold">
                      <li className="flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-brand-600 flex-shrink-0" /> Acceso a ediciones demo
                      </li>
                      <li className="flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-brand-600 flex-shrink-0" /> 1 Periódico activo
                      </li>
                      <li className="flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-brand-600 flex-shrink-0" /> Soporte comunitario
                      </li>
                    </ul>
                  </div>
                  <button className="w-full py-2 text-xs font-bold text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors">
                    Elegir plan
                  </button>
                </div>

                {/* Profesional */}
                <div className="bg-white border-2 border-brand-500 rounded-2xl p-5 flex flex-col justify-between relative shadow-md sm:-translate-y-2">
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-brand-500 text-dark-900 text-[8px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-full">
                    Recomendado
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-base mb-0.5">Profesional</h3>
                    <p className="text-[10px] text-slate-400 mb-4 font-semibold">Monetización completa y control</p>
                    <div className="flex items-baseline mb-4">
                      <span className="text-2xl font-black text-slate-950">US$ 49</span>
                      <span className="text-xs text-slate-400 ml-1">/mes</span>
                    </div>
                    
                    <ul className="space-y-2.5 mb-6 text-[10px] text-slate-600 font-semibold">
                      <li className="flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-brand-600 flex-shrink-0" /> Ediciones ilimitadas
                      </li>
                      <li className="flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-brand-600 flex-shrink-0" /> Pasarela integrada
                      </li>
                      <li className="flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-brand-600 flex-shrink-0" /> Soporte personalizado
                      </li>
                    </ul>
                  </div>
                  <button className="w-full py-2 text-xs font-bold text-dark-900 bg-brand-500 hover:bg-brand-400 rounded-lg transition-all">
                    Elegir plan
                  </button>
                </div>

                {/* Empresarial */}
                <div className="bg-white border border-slate-200 rounded-2xl p-5 flex flex-col justify-between hover:shadow-md transition-shadow">
                  <div>
                    <h3 className="font-bold text-slate-900 text-base mb-0.5">Empresarial</h3>
                    <p className="text-[10px] text-slate-400 mb-4 font-semibold">Soporte y volumen masivo</p>
                    <div className="flex items-baseline mb-4">
                      <span className="text-2xl font-black text-slate-950">US$ 99</span>
                      <span className="text-xs text-slate-400 ml-1">/mes</span>
                    </div>
                    
                    <ul className="space-y-2.5 mb-6 text-[10px] text-slate-600 font-semibold">
                      <li className="flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-brand-600 flex-shrink-0" /> Multi-empresa habilitado
                      </li>
                      <li className="flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-brand-600 flex-shrink-0" /> API & Webhooks
                      </li>
                      <li className="flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-brand-600 flex-shrink-0" /> SLA de 99.9%
                      </li>
                    </ul>
                  </div>
                  <button className="w-full py-2 text-xs font-bold text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors">
                    Elegir plan
                  </button>
                </div>

              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Benefits / Features Grid */}
      <section className="py-20 bg-slate-50 border-t border-slate-200/50">
        <div className="max-w-7xl mx-auto px-6">
          
          <div className="text-center max-w-xl mx-auto mb-16">
            <span className="text-xs font-bold text-brand-700 uppercase tracking-widest">Características</span>
            <h2 className="text-3xl font-black text-slate-900 mt-2 mb-3">
              Todo lo que necesitas para tu periódico digital
            </h2>
            <p className="text-xs text-slate-500 font-semibold">
              Herramientas de última generación para la distribución digital segura
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
            {[
              { icon: Shield, title: 'Visor protegido', desc: 'Evita la copia o descarga no autorizada de tus PDFs originales.' },
              { icon: CreditCard, title: 'Pagos integrados', desc: 'Conexión directa con pasarelas de pago para ventas individuales o suscripción.' },
              { icon: Layers, title: 'Gestión multi-edición', desc: 'Sube y clasifica tus números por fecha, volumen o categorías específicas.' },
              { icon: Activity, title: 'Dashboard analítico', desc: 'Métricas completas de lecturas, descargas e ingresos generados.' },
              { icon: Share2, title: 'API / Webhooks', desc: 'Integra el lector digital en tu sitio web corporativo o aplicaciones móviles.' },
              { icon: Key, title: 'Control de accesos', desc: 'Define quién lee, cuándo lee y bajo qué restricciones específicas.' }
            ].map((feat, i) => {
              const Icon = feat.icon;
              return (
                <div key={i} className="bg-white border border-slate-200/60 p-6 rounded-2xl shadow-sm hover:shadow-md transition-all flex flex-col items-start">
                  <div className="w-10 h-10 bg-brand-500/10 rounded-xl flex items-center justify-center text-brand-700 mb-4">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-slate-900 mb-2">{feat.title}</h3>
                  <p className="text-xs text-slate-500 font-semibold leading-relaxed">{feat.desc}</p>
                </div>
              );
            })}
          </div>

        </div>
      </section>

      {/* CTA Final Bottom Banner */}
      <section className="py-16 bg-slate-900 text-white relative">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-800 via-slate-900 to-slate-950 opacity-90 pointer-events-none"></div>
        <div className="max-w-5xl mx-auto px-6 relative z-10 text-center space-y-6">
          <h2 className="text-3xl font-black tracking-tight sm:text-4xl text-white">
            ¿Listo para transformar tu medio?
          </h2>
          <p className="text-slate-300 text-sm max-w-xl mx-auto font-semibold opacity-80 leading-relaxed">
            Digitaliza tus contenidos de manera segura y abre nuevos canales de monetización en minutos.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-2 max-w-[400px] mx-auto">
            <Link to="/register" className="px-6 py-3.5 text-sm font-bold text-dark-900 bg-brand-500 hover:bg-brand-400 rounded-xl transition-all shadow-md shadow-brand-500/10">
              Crear mi periódico gratis
            </Link>
            <a href="#demo" className="px-6 py-3.5 text-sm font-semibold text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl transition-all">
              Ver demo en vivo
            </a>
          </div>
        </div>
      </section>



    </div>
  );
};

export default Landing;
