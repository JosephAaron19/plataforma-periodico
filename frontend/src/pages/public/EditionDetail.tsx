import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  ArrowLeft, MapPin, Calendar, BookOpen, Users, TrendingUp, Activity, 
  Award, Check, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Maximize2, 
  Lock, Shield, Sparkles, CheckCircle2
} from 'lucide-react';
import { useSimulation } from '../../contexts/SimulationContext';

const EditionDetail: React.FC = () => {
  // Interactive States
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [zoom, setZoom] = useState<number>(100);
  const [hasAccess, setHasAccess] = useState<boolean>(false);
  const [purchaseLoading, setPurchaseLoading] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [hoveredDevice, setHoveredDevice] = useState<'laptop' | 'mobile' | null>(null);

  // Custom Image State from simulation context
  const { customImage, setCustomImage } = useSimulation();

  const totalPages = 32;

  // Pages simulation content
  const pageContents: { [key: number]: { headline: string; summary: string; category: string; content: string } } = {
    1: {
      category: 'PORTADA',
      headline: 'Economía local muestra crecimiento del 2.8% en el primer trimestre del año',
      summary: 'El informe del BCRP destaca el dinamismo de diversos sectores económicos en la región, superando las proyecciones iniciales gracias a la reactivación comercial.',
      content: 'Las inversiones en manufactura, comercio minorista y servicios impulsaron este avance. Expertos prevén estabilidad en los precios de la canasta básica durante el próximo bimestre.'
    },
    2: {
      category: 'POLÍTICA',
      headline: 'Gobierno Regional anuncia reforma de infraestructura vial para conectar 8 provincias',
      summary: 'El plan de inversión de más de 45 millones de soles busca asfaltar vías de acceso rurales clave y reducir a la mitad los tiempos de transporte comercial.',
      content: 'La licitación pública comenzará a finales del próximo mes. Alcaldes provinciales celebran la iniciativa pero exigen auditorías independientes para evitar retrasos de ejecución.'
    },
    3: {
      category: 'EDITORIAL',
      headline: 'El futuro de la prensa digital: Desafíos y oportunidades en la era del SaaS',
      summary: 'La transición de los periódicos en papel hacia plataformas digitales no es solo un cambio de formato, sino una revolución en el modelo de monetización y seguridad de contenidos.',
      content: 'Los lectores exigen accesos seguros y lecturas optimizadas en sus celulares. Proteger las ediciones en PDF y fidelizar mediante suscripciones recurrentes marcará la supervivencia periodística.'
    },
    4: {
      category: 'DEPORTES',
      headline: 'Club local clasifica a la gran final del Torneo de Clausura tras agónico triunfo',
      summary: 'Con un gol en el minuto 94, la escuadra regional superó al líder de la tabla y aseguró su pase al play-off definitorio en el Estadio Nacional.',
      content: 'El director técnico agradeció la entrega del plantel. La afición prepara caravanas para acompañar al equipo en el partido de ida programado para este domingo.'
    },
    5: {
      category: 'CULTURA',
      headline: 'Festival Internacional de Teatro reúne a más de 10 mil espectadores en plazas públicas',
      summary: 'Compañías de cinco países deleitaron al público con montajes experimentales, talleres interactivos y obras infantiles de acceso gratuito.',
      content: 'La clausura del evento contó con una puesta en escena de danzas tradicionales y fuegos artificiales. El patronato cultural ya proyecta la edición 2027.'
    }
  };

  // Safe fallback for pages without defined mocked content
  const getPageData = (page: number) => {
    return pageContents[page] || {
      category: `SECCIÓN GENERAL - Pág. ${page}`,
      headline: `Reporte Especial: Desarrollo de Proyectos Regionales y Comunitarios`,
      summary: `Detalles e informes estadísticos de avance sectorial correspondientes al número de edición #125.`,
      content: `Este contenido es exclusivo para miembros registrados. La Voz del Sur promueve periodismo independiente de libre acceso bajo suscripciones integradas.`
    };
  };

  const activePageData = getPageData(currentPage);

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(prev => prev + 1);
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(prev => prev - 1);
    }
  };

  const handleZoomIn = () => {
    if (zoom < 150) setZoom(prev => prev + 25);
  };

  const handleZoomOut = () => {
    if (zoom > 75) setZoom(prev => prev - 25);
  };

  const simulatePurchase = () => {
    setPurchaseLoading(true);
    setTimeout(() => {
      setHasAccess(true);
      setPurchaseLoading(false);
    }, 1500);
  };

  // Image Upload handlers
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
    <div className="bg-[#030712] min-h-screen text-gray-800 font-sans py-8 sm:py-12 relative px-4 sm:px-6">
      
      {/* Background radial effects for premium layout */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-brand-500/5 rounded-full blur-[140px] pointer-events-none"></div>

      {/* Main light-themed modal-like container */}
      <div className="max-w-6xl mx-auto bg-[#f8fafc] rounded-[2rem] border border-gray-200/80 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.6)] p-6 sm:p-10 relative z-10">
        
        {/* Header toolbar within the modal box */}
        <div className="flex justify-between items-center mb-8 border-b border-gray-250/60 pb-4">
          <Link 
            to="/" 
            className="inline-flex items-center text-sm font-bold text-gray-500 hover:text-gray-900 transition-colors gap-2 group font-sans"
          >
            <ArrowLeft className="w-4 h-4 transform group-hover:-translate-x-1 transition-transform text-brand-600" />
            Volver al catálogo de periódicos
          </Link>
          <Link to="/" className="p-1 text-gray-400 hover:text-gray-900 transition-colors text-xl font-bold flex items-center justify-center w-8 h-8 rounded-lg hover:bg-gray-200/50" title="Cerrar">
            ×
          </Link>
        </div>

        {/* Inner Layout Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-start">
          
          {/* LEFT COLUMN: Metadata, statistics & details */}
          <div className="lg:col-span-7 xl:col-span-8 space-y-8">
            
            {/* Header info section */}
            <div className="flex flex-col sm:flex-row gap-6 items-start sm:items-center">
              {/* Simulated newspaper logo / thumbnail */}
              <div className="w-24 h-24 bg-[#090d16] rounded-2xl flex items-center justify-center border border-gray-800 shadow-xl flex-shrink-0 relative overflow-hidden group">
                {customImage ? (
                  <img src={customImage} className="w-full h-full object-cover" alt="Logo de periódico personalizado" />
                ) : (
                  <>
                    <div className="absolute inset-0 bg-gradient-to-tr from-brand-900 to-dark-900 opacity-20"></div>
                    {/* Simulated visual newspaper inside logo box */}
                    <div className="w-16 h-18 bg-white rounded shadow p-1 flex flex-col justify-between">
                      <div className="border-b border-gray-900 pb-0.5 text-center">
                        <span className="font-serif font-black text-[5px] text-gray-955 block tracking-tighter leading-none text-gray-900">LA VOZ DEL SUR</span>
                      </div>
                      <div className="flex-1 flex flex-col gap-0.5 py-1 justify-center">
                        <div className="h-0.5 bg-gray-300 w-full"></div>
                        <div className="h-0.5 bg-gray-300 w-4/5"></div>
                        <div className="h-0.5 bg-brand-500 w-2/3"></div>
                      </div>
                      <span className="text-[3px] text-gray-400 text-right block">#125</span>
                    </div>
                  </>
                )}
              </div>

              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <h1 className="text-3xl font-black text-gray-900 tracking-tight">La Voz del Sur</h1>
                </div>
                <p className="text-brand-600 font-bold text-sm mt-1">
                  Información que conecta a nuestra comunidad
                </p>

                <div className="flex flex-wrap gap-2 text-[11px] text-gray-500 mt-4 font-bold">
                  <span className="flex items-center gap-1.5 bg-gray-150 px-3 py-1 rounded-lg">
                    <MapPin className="w-3.5 h-3.5 text-brand-600" /> Arequipa, Perú
                  </span>
                  <span className="flex items-center gap-1.5 bg-gray-150 px-3 py-1 rounded-lg">
                    <Calendar className="w-3.5 h-3.5 text-brand-600" /> Desde 2010
                  </span>
                  <span className="flex items-center gap-1.5 bg-[#f0fdfa] text-brand-700 border border-brand-100 px-3 py-1 rounded-lg">
                    Edición #125 - 15 Mayo 2026
                  </span>
                </div>
              </div>
            </div>

            {/* Custom Image Uploader / Simulator Widget */}
            <div className="bg-white p-6 rounded-2xl border border-gray-200/60 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-brand-600 animate-pulse" /> Panel de Simulación de Diseño
                </h3>
                {customImage && (
                  <button 
                    onClick={handleResetImage}
                    className="text-xs text-red-500 hover:text-red-700 font-bold"
                  >
                    Restablecer diseño predeterminado
                  </button>
                )}
              </div>
              <p className="text-[11px] text-gray-500 leading-relaxed">
                Ingresa una imagen personalizada para ver cómo se coloca y adapta de forma automática e integrada dentro del logotipo, la pantalla de laptop, el teléfono celular y el visor modal a pantalla completa.
              </p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                
                {/* File Upload Option */}
                <div className="flex flex-col justify-center p-4 bg-[#f8fafc] border border-gray-150 rounded-xl">
                  <label className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2 block">
                    Cargar archivo local
                  </label>
                  <input 
                    type="file" 
                    accept="image/*" 
                    onChange={handleImageUpload}
                    className="block w-full text-xs text-gray-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-lg file:border-0
                      file:text-xs file:font-semibold
                      file:bg-brand-50 file:text-brand-700
                      hover:file:bg-brand-100 cursor-pointer"
                  />
                </div>

                {/* URL Paste Option */}
                <div className="flex flex-col justify-center p-4 bg-[#f8fafc] border border-gray-150 rounded-xl">
                  <label className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2 block">
                    Pegar enlace de imagen (URL)
                  </label>
                  <input 
                    type="text" 
                    placeholder="https://ejemplo.com/portada.jpg" 
                    onChange={handleUrlChange}
                    className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-700 placeholder-gray-400 focus:outline-none focus:border-brand-400 focus:ring-1 focus:ring-brand-400 font-medium"
                  />
                </div>

              </div>
            </div>

            <p className="text-gray-600 text-sm leading-relaxed">
              La Voz del Sur es un medio independiente que informa con objetividad y compromiso sobre los hechos más importantes de Arequipa y la región sur del Perú. Nuestro propósito es dar voz a la comunidad y promover el desarrollo local.
            </p>

            {/* Badges / Stats grid */}
            <div className="bg-white p-6 rounded-2xl border border-gray-200/60 shadow-sm">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                
                <div className="bg-[#f8fafc] border border-gray-150 p-4 rounded-xl flex flex-col gap-2 items-center text-center shadow-sm">
                  <div className="p-2.5 bg-brand-50 text-brand-600 rounded-xl">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <span className="text-2xl font-black text-gray-900">+680</span>
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider font-extrabold">Ediciones publicadas</span>
                </div>

                <div className="bg-[#f8fafc] border border-gray-150 p-4 rounded-xl flex flex-col gap-2 items-center text-center shadow-sm">
                  <div className="p-2.5 bg-brand-50 text-brand-600 rounded-xl">
                    <Users className="w-5 h-5" />
                  </div>
                  <span className="text-2xl font-black text-gray-900">+25K</span>
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider font-extrabold">Lectores mensuales</span>
                </div>

                <div className="bg-[#f8fafc] border border-gray-150 p-4 rounded-xl flex flex-col gap-2 items-center text-center shadow-sm">
                  <div className="p-2.5 bg-brand-50 text-brand-600 rounded-xl">
                    <Calendar className="w-5 h-5" />
                  </div>
                  <span className="text-2xl font-black text-gray-900">14 años</span>
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider font-extrabold">Informando a la región</span>
                </div>

                <div className="bg-[#f8fafc] border border-gray-150 p-4 rounded-xl flex flex-col gap-2 items-center text-center shadow-sm">
                  <div className="p-2.5 bg-brand-50 text-brand-600 rounded-xl">
                    <Award className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-black text-gray-900 leading-tight">Premio Regional de Periodismo 2022</span>
                  <span className="text-[9px] text-gray-400 font-medium">Excelencia en prensa</span>
                </div>

              </div>
            </div>

            {/* Sub-columns grid (About Editor & Sections) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-2">
              
              {/* About Publisher */}
              <div className="space-y-4 text-left">
                <h3 className="text-lg font-bold text-gray-900 tracking-tight">Sobre La Voz del Sur</h3>
                <p className="text-gray-600 text-xs leading-relaxed">
                  Fundado en mayo de 2010, La Voz del Sur nació con la misión de ofrecer periodismo riguroso, ético y cercano a la gente. A lo largo de los años, hemos evolucionado junto a nuestra comunidad, adoptando nuevas tecnologías para seguir cumpliendo nuestra misión en la era digital.
                </p>
                
                <div className="space-y-2.5 pt-2">
                  <div className="flex items-center gap-2.5 text-xs font-bold text-gray-700">
                    <div className="bg-green-100 p-0.5 rounded-full text-green-600">
                      <Check className="w-3 h-3" />
                    </div>
                    <span>Equipo periodístico con más de 20 profesionales</span>
                  </div>
                  <div className="flex items-center gap-2.5 text-xs font-bold text-gray-700">
                    <div className="bg-green-100 p-0.5 rounded-full text-green-600">
                      <Check className="w-3 h-3" />
                    </div>
                    <span>Cobertura en Arequipa y 8 provincias</span>
                  </div>
                  <div className="flex items-center gap-2.5 text-xs font-bold text-gray-700">
                    <div className="bg-green-100 p-0.5 rounded-full text-green-600">
                      <Check className="w-3 h-3" />
                    </div>
                    <span>Periodismo verificado y responsable</span>
                  </div>
                  <div className="flex items-center gap-2.5 text-xs font-bold text-gray-700">
                    <div className="bg-green-100 p-0.5 rounded-full text-green-600">
                      <Check className="w-3 h-3" />
                    </div>
                    <span>Comprometidos con la comunidad</span>
                  </div>
                </div>
              </div>

              {/* Sections list */}
              <div className="flex flex-col">
                <h3 className="text-lg font-bold text-gray-900 tracking-tight mb-4">Secciones principales</h3>
                
                <div className="grid grid-cols-2 gap-3 flex-grow">
                  {[
                    { label: 'Locales', icon: MapPin },
                    { label: 'Política', icon: Users },
                    { label: 'Economía', icon: TrendingUp },
                    { label: 'Deportes', icon: Activity },
                    { label: 'Cultura', icon: BookOpen },
                    { label: 'Opinión', icon: Award },
                  ].map((sec, idx) => (
                    <div 
                      key={idx} 
                      className="flex items-center gap-2.5 p-3 bg-white border border-gray-150 hover:border-brand-400 rounded-xl transition-all cursor-pointer shadow-sm hover:shadow"
                    >
                      <sec.icon className="w-4 h-4 text-brand-600" />
                      <span className="text-xs font-bold text-gray-700">{sec.label}</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>

            {/* Footer row (Premium qualities) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 bg-white border border-gray-200/60 p-6 rounded-2xl shadow-inner">
              
              <div className="flex gap-3">
                <div className="p-2 bg-brand-500/10 rounded-xl text-brand-600 flex-shrink-0 self-start">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-gray-955 uppercase tracking-wider">Acceso inmediato</h4>
                  <p className="text-[10px] text-gray-500 leading-normal mt-1 font-medium">
                    Obtén acceso al instante desde cualquier dispositivo.
                  </p>
                </div>
              </div>

              <div className="flex gap-3 border-t md:border-t-0 md:border-l border-gray-200/60 pt-4 md:pt-0 md:pl-6">
                <div className="p-2 bg-brand-500/10 rounded-xl text-brand-600 flex-shrink-0 self-start">
                  <BookOpen className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-gray-955 uppercase tracking-wider">Lectura optimizada</h4>
                  <p className="text-[10px] text-gray-500 leading-normal mt-1 font-medium">
                    Visor rápido, intuitivo y adaptado para una mejor experiencia.
                  </p>
                </div>
              </div>

              <div className="flex gap-3 border-t md:border-t-0 md:border-l border-gray-200/60 pt-4 md:pt-0 md:pl-6">
                <div className="p-2 bg-brand-500/10 rounded-xl text-brand-600 flex-shrink-0 self-start">
                  <Shield className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-gray-955 uppercase tracking-wider">Pago 100% seguro</h4>
                  <p className="text-[10px] text-gray-500 leading-normal mt-1 font-medium">
                    Tus pagos están protegidos con tecnología de cifrado.
                  </p>
                </div>
              </div>

            </div>

          </div>

          {/* RIGHT COLUMN: Laptop preview & smartphone container */}
          <div className="lg:col-span-5 xl:col-span-4 space-y-6">
            
            {/* Device header metadata matching the mockup */}
            <div className="space-y-1 text-left">
              <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Edición más reciente</span>
              <h2 className="text-2xl font-black text-gray-900 tracking-tight">Edición #125</h2>
              <p className="text-xs text-gray-500 font-semibold">15 Mayo 2026</p>
            </div>

            {/* Main Interactive Laptop Mockup Container */}
            <div 
              className={`bg-[#0b1220] p-5 rounded-3xl border transition-all duration-300 shadow-xl ${
                hoveredDevice === 'laptop' ? 'border-brand-500/40 shadow-brand-500/5' : 'border-white/5'
              }`}
              onMouseEnter={() => setHoveredDevice('laptop')}
              onMouseLeave={() => setHoveredDevice(null)}
            >
              <div className="flex justify-between items-center mb-4 text-left">
                <div>
                  <span className="text-[9px] text-brand-400 uppercase tracking-widest font-extrabold">
                    Vista previa de edición
                  </span>
                  <h2 className="text-[11px] font-bold text-white">Edición #125 - Portada</h2>
                </div>
                <button 
                  onClick={() => setIsFullscreen(true)}
                  className="p-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-all"
                  title="Expandir visor"
                >
                  <Maximize2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Laptop Body Mockup */}
              <div className="relative w-full mx-auto select-none">
                
                {/* Screen frame */}
                <div className="w-full bg-[#080c14] border-[6px] border-gray-800 rounded-t-2xl shadow-2xl relative overflow-hidden aspect-[4/3] flex flex-col">
                  
                  {/* Browser simulated bar */}
                  <div className="bg-[#0f172a] h-6 px-3 border-b border-white/5 flex items-center justify-between text-[7px] text-gray-500 flex-shrink-0">
                    <div className="flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500/40"></span>
                      <span className="w-1.5 h-1.5 rounded-full bg-yellow-500/40"></span>
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500/40"></span>
                    </div>
                    <span className="bg-black/20 px-3 py-0.5 rounded text-gray-400 font-mono text-[6px]">lavozdelsur-ed125.pdf</span>
                    <span className="opacity-0">extra</span>
                  </div>

                  {/* Inside Screen Content Wrapper */}
                  <div className="flex-grow flex bg-[#121926] relative overflow-hidden">
                    
                    {/* Simulator sidebar panel */}
                    <div className="w-8 bg-[#090e18] border-r border-white/5 flex flex-col items-center py-2 gap-3 flex-shrink-0 text-[10px] text-gray-600">
                      <div className="p-1 text-brand-400 bg-brand-500/10 rounded"><BookOpen className="w-3 h-3" /></div>
                      <div className="p-1 hover:text-white transition-colors cursor-pointer"><Users className="w-3 h-3" /></div>
                      <div className="p-1 hover:text-white transition-colors cursor-pointer"><TrendingUp className="w-3 h-3" /></div>
                      <div className="p-1 hover:text-white transition-colors cursor-pointer"><Award className="w-3 h-3" /></div>
                    </div>

                    {/* Simulating the zoom and page state in CSS */}
                    <div 
                      className="flex-grow p-3 overflow-hidden flex flex-col justify-between transition-transform duration-300"
                      style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'center center' }}
                    >
                      {customImage ? (
                        <div className="w-full h-full bg-white flex items-center justify-center overflow-hidden rounded shadow-lg">
                          <img src={customImage} className="w-full h-full object-contain" alt="Portada personalizada" />
                        </div>
                      ) : (
                        <div className="border border-black/20 bg-[#fafafa] text-dark-900 p-2.5 rounded shadow-lg flex-grow flex flex-col justify-between">
                          
                          {/* Newspaper Banner */}
                          <div className="border-b border-dark-900/10 pb-1 text-center flex-shrink-0">
                            <h4 className="font-serif text-[14px] font-extrabold text-black tracking-tight leading-none">
                              LA VOZ DEL SUR
                            </h4>
                            <div className="flex justify-between items-center text-[5px] text-gray-500 font-bold uppercase mt-1 tracking-wider">
                              <span>PORTADA REGIONAL</span>
                              <span>EDICIÓN #125</span>
                              <span>15 MAYO 2026</span>
                            </div>
                          </div>

                          {/* Page Body contents changing based on page state */}
                          <div className="flex-grow flex flex-col justify-center py-1.5 space-y-1 overflow-hidden text-left">
                            <span className="text-[4px] font-bold uppercase px-1 py-0.2 bg-brand-500/10 text-brand-900 rounded self-start tracking-wider">
                              {activePageData.category}
                            </span>
                            <h5 className="font-bold text-[7px] text-dark-900 font-sans tracking-tight leading-tight uppercase leading-tight">
                              {activePageData.headline}
                            </h5>
                            <p className="text-[6px] text-gray-600 leading-snug font-medium italic">
                              {activePageData.summary}
                            </p>
                            <p className="text-[4.5px] text-gray-500 leading-normal line-clamp-3">
                              {activePageData.content}
                            </p>
                          </div>

                          {/* Page number footer */}
                          <div className="border-t border-dark-900/10 pt-1 text-[4px] text-gray-400 font-bold flex justify-between items-center flex-shrink-0">
                            <span>LA VOZ DEL SUR S.A.C.</span>
                            <span>PÁGINA {currentPage} DE {totalPages}</span>
                          </div>

                        </div>
                      )}
                    </div>

                  </div>

                  {/* Device Control toolbar */}
                  <div className="bg-[#0f172a] h-10 border-t border-white/5 flex items-center justify-between px-3 text-[10px] text-gray-400 flex-shrink-0">
                    <div className="flex items-center gap-1">
                      <button 
                        onClick={handleZoomOut} 
                        className="p-1 hover:text-white bg-white/5 hover:bg-white/10 rounded transition-colors"
                        disabled={zoom <= 75}
                      >
                        <ZoomOut className="w-3 h-3" />
                      </button>
                      <span className="text-[8px] font-semibold w-7 text-center">{zoom}%</span>
                      <button 
                        onClick={handleZoomIn} 
                        className="p-1 hover:text-white bg-white/5 hover:bg-white/10 rounded transition-colors"
                        disabled={zoom >= 150}
                      >
                        <ZoomIn className="w-3 h-3" />
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <button 
                        onClick={handlePrevPage} 
                        className="p-1 hover:text-white bg-white/5 hover:bg-white/10 rounded disabled:opacity-30 transition-all"
                        disabled={currentPage <= 1}
                      >
                        <ChevronLeft className="w-3 h-3" />
                      </button>
                      <span className="font-bold text-[8px] tracking-widest text-center min-w-[30px]">
                        {currentPage} / {totalPages}
                      </span>
                      <button 
                        onClick={handleNextPage} 
                        className="p-1 hover:text-white bg-white/5 hover:bg-white/10 rounded disabled:opacity-30 transition-all"
                        disabled={currentPage >= totalPages}
                      >
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    </div>

                    <button 
                      onClick={() => setIsFullscreen(true)}
                      className="p-1 hover:text-white bg-white/5 hover:bg-white/10 rounded transition-colors"
                    >
                      <Maximize2 className="w-3 h-3" />
                    </button>
                  </div>

                </div>

                {/* Laptop base */}
                <div className="w-[106%] -ml-[3%] h-2.5 bg-gray-700 rounded-b-2xl shadow-xl border-t border-gray-600"></div>
                <div className="w-[24%] mx-auto h-1 bg-gray-800 rounded-b-lg"></div>

              </div>
            </div>

            {/* Premium SmartPhone Mockup & Pricing access details */}
            <div 
              className={`bg-[#050912] p-6 rounded-3xl border transition-all duration-300 shadow-xl overflow-hidden relative ${
                hoveredDevice === 'mobile' ? 'border-brand-500/40 shadow-brand-500/5' : 'border-white/5'
              }`}
              onMouseEnter={() => setHoveredDevice('mobile')}
              onMouseLeave={() => setHoveredDevice(null)}
            >
              
              {/* Decorative side effect */}
              <div className="absolute -bottom-8 -left-8 w-24 h-24 bg-brand-500/10 rounded-full blur-xl pointer-events-none"></div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-6 items-center">
                
                {/* Smartphone Device Mockup */}
                <div className="relative mx-auto w-[160px] aspect-[9/18] bg-gray-900 border-[6px] border-gray-800 rounded-[2.5rem] shadow-2xl overflow-hidden flex-shrink-0 flex flex-col justify-between p-2">
                  
                  {/* Phone speaker notch */}
                  <div className="absolute top-1 left-1/2 -translate-x-1/2 w-14 h-3.5 bg-gray-800 rounded-b-xl flex items-center justify-center gap-1 z-20">
                    <span className="w-1.5 h-1.5 rounded-full bg-black/40"></span>
                    <span className="w-5 h-0.5 bg-black/40 rounded-full"></span>
                  </div>

                  {/* Inside phone screen content */}
                  <div className="flex-grow flex flex-col justify-between bg-[#121926] rounded-[1.8rem] p-2.5 pt-6 text-[8px] text-gray-400 overflow-hidden relative">
                    {customImage ? (
                      <div className="w-full h-full bg-white flex items-center justify-center overflow-hidden rounded-[1.3rem]">
                        <img src={customImage} className="w-full h-full object-contain" alt="Portada personalizada" />
                      </div>
                    ) : (
                      <div className="bg-[#fafafa] text-dark-900 p-2 rounded shadow-md flex-grow flex flex-col justify-between border border-black/10">
                        
                        <div className="border-b border-dark-900/10 pb-1 text-center flex-shrink-0">
                          <h6 className="font-serif text-[10px] font-extrabold leading-none text-black">LA VOZ DEL SUR</h6>
                          <span className="text-[4px] text-gray-500 tracking-wider">EDICIÓN #125</span>
                        </div>

                        <div className="flex-grow flex flex-col justify-center py-1.5 space-y-1 overflow-hidden text-left">
                          <span className="text-[4px] font-bold uppercase px-1 py-0.2 bg-brand-500/10 text-brand-900 rounded self-start">
                            {activePageData.category}
                          </span>
                          <h6 className="font-bold text-[7px] text-dark-900 tracking-tight leading-tight uppercase line-clamp-2">
                            {activePageData.headline}
                          </h6>
                          <p className="text-[4.5px] text-gray-500 leading-normal line-clamp-3">
                            {activePageData.summary}
                          </p>
                        </div>

                        <div className="border-t border-dark-900/10 pt-1 text-[4px] text-gray-400 font-bold flex justify-between items-center flex-shrink-0">
                          <span>LVS MOVIL</span>
                          <span>PÁG. {currentPage}</span>
                        </div>

                      </div>
                    )}
                  </div>
                </div>

                {/* Pricing / CTA Access details */}
                <div className="space-y-4">
                  <div className="space-y-1 text-left">
                    <span className="text-[10px] text-brand-400 uppercase tracking-widest font-extrabold">
                      Acceso a esta edición
                    </span>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-black text-white">US$ 2.50</span>
                    </div>
                  </div>

                  <div className="space-y-3 pt-2">
                    {hasAccess ? (
                      <button 
                        className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-bold text-dark-900 bg-green-400 hover:bg-green-300 transition-all cursor-default"
                        disabled
                      >
                        <CheckCircle2 className="w-4 h-4 mr-2" /> Acceso habilitado
                      </button>
                    ) : (
                      <button 
                        onClick={simulatePurchase}
                        disabled={purchaseLoading}
                        className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-bold text-dark-900 bg-brand-500 hover:bg-brand-400 hover:shadow-brand-500/10 focus:outline-none transition-all disabled:opacity-75"
                      >
                        {purchaseLoading ? (
                          <span className="flex items-center gap-2">
                            <span className="w-4 h-4 border-2 border-dark-900 border-t-transparent rounded-full animate-spin"></span>
                            Procesando...
                          </span>
                        ) : (
                          <span className="flex items-center gap-2">
                            Comprar acceso
                          </span>
                        )}
                      </button>
                    )}

                    <div className="flex flex-col items-center gap-2">
                      <div className="flex items-center justify-center gap-1 text-[9px] text-gray-500 font-bold uppercase tracking-wider">
                        <Lock className="w-3.5 h-3.5 text-brand-400" /> Pago seguro con Stripe
                      </div>
                    </div>
                  </div>

                </div>

              </div>

            </div>

            {/* SaaS Banner promote (Light-green banner from mockup) */}
            <div className="bg-[#f0fdfa] border border-[#ccfbf1] p-6 rounded-3xl shadow-sm relative overflow-hidden text-gray-800">
              <div className="absolute top-0 right-0 w-20 h-20 bg-brand-500/5 rounded-full blur-xl pointer-events-none"></div>
              
              <div className="space-y-4">
                <h4 className="text-sm font-extrabold text-gray-955 tracking-tight text-left">
                  ¿Tienes una empresa o eres un medio?
                </h4>
                
                <p className="text-gray-500 text-xs leading-relaxed font-medium text-left">
                  Publica tus ediciones y monetiza tu contenido con DigitalSaaS.
                </p>

                <div className="text-left">
                  <a 
                    href="/#precios"
                    className="inline-flex items-center text-xs font-bold text-brand-600 hover:text-brand-700 transition-colors gap-1.5 group"
                  >
                    Conoce nuestros planes 
                    <ChevronRight className="w-3.5 h-3.5 transform group-hover:translate-x-1 transition-transform" />
                  </a>
                </div>
              </div>
            </div>

          </div>

        </div>

      </div>

      {/* FULLSCREEN PREVIEW OVERLAY MODAL */}
      {isFullscreen && (
        <div className="fixed inset-0 z-[100] bg-black/95 backdrop-blur-md flex flex-col justify-between p-6 select-none animate-in fade-in duration-200">
          
          {/* Fullscreen Header */}
          <div className="max-w-6xl mx-auto w-full flex items-center justify-between border-b border-white/10 pb-4 text-gray-400 flex-shrink-0">
            <div>
              <h2 className="text-lg font-serif font-extrabold text-white">LA VOZ DEL SUR</h2>
              <p className="text-xs text-brand-400 font-semibold uppercase tracking-wider">
                Edición #125 - {activePageData.category}
              </p>
            </div>

            <button 
              onClick={() => setIsFullscreen(false)}
              className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-white font-bold text-xs transition-all border border-white/10"
            >
              Cerrar Vista Completa
            </button>
          </div>

          {/* Fullscreen Body Newspaper Page emulation */}
          <div className="max-w-2xl mx-auto w-full flex-grow flex items-center justify-center p-4">
            {customImage ? (
              <div className="bg-white p-4 rounded-xl shadow-2xl border border-white/15 w-full aspect-[3/4] flex items-center justify-center max-h-[70vh] overflow-hidden">
                <img src={customImage} className="w-full h-full object-contain" alt="Portada personalizada" />
              </div>
            ) : (
              <div className="bg-[#fafafa] text-dark-900 p-8 rounded-xl shadow-2xl border border-white/15 w-full aspect-[3/4] flex flex-col justify-between max-h-[70vh]">
                
                <div className="border-b-2 border-dark-900 pb-3 text-center flex-shrink-0">
                  <h3 className="font-serif text-3xl font-extrabold text-black tracking-tight leading-none">
                    LA VOZ DEL SUR
                  </h3>
                  <div className="flex justify-between items-center text-[8px] text-gray-500 font-bold uppercase mt-2 tracking-widest">
                    <span>PORTADA REGIONAL</span>
                    <span>EDICIÓN #125</span>
                    <span>15 MAYO 2026</span>
                  </div>
                </div>

                <div className="flex-grow flex flex-col justify-center py-6 space-y-3">
                  <span className="text-[9px] font-extrabold uppercase px-2 py-0.5 bg-brand-500/25 text-brand-900 rounded self-start tracking-widest">
                    {activePageData.category}
                  </span>
                  <h4 className="font-extrabold text-[16px] text-dark-900 font-sans tracking-tight leading-tight uppercase text-left">
                    {activePageData.headline}
                  </h4>
                  <p className="text-[10px] text-gray-600 leading-relaxed font-semibold italic text-left">
                    {activePageData.summary}
                  </p>
                  <p className="text-[9px] text-gray-500 leading-relaxed text-left">
                    {activePageData.content}
                  </p>
                </div>

                <div className="border-t-2 border-dark-900/10 pt-3 text-[8px] text-gray-400 font-extrabold flex justify-between items-center flex-shrink-0">
                  <span>LA VOZ DEL SUR S.A.C.</span>
                  <span>PÁGINA {currentPage} DE {totalPages}</span>
                </div>

              </div>
            )}
          </div>

          {/* Fullscreen Navigation Footer Controls */}
          <div className="max-w-6xl mx-auto w-full flex items-center justify-between border-t border-white/10 pt-4 text-gray-400 flex-shrink-0">
            <div className="text-xs">
              Usa los botones o flechas del teclado para navegar
            </div>

            <div className="flex items-center gap-4">
              <button 
                onClick={handlePrevPage} 
                className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl disabled:opacity-30 transition-all text-xs font-bold"
                disabled={currentPage <= 1}
              >
                Anterior
              </button>
              
              <span className="font-bold text-sm tracking-widest text-white">
                {currentPage} / {totalPages}
              </span>
              
              <button 
                onClick={handleNextPage} 
                className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl disabled:opacity-30 transition-all text-xs font-bold"
                disabled={currentPage >= totalPages}
              >
                Siguiente
              </button>
            </div>

            <div className="text-xs text-brand-400 font-semibold">
              DigitalSaaS Visor Protegido
            </div>
          </div>

        </div>
      )}

    </div>
  );
};

export default EditionDetail;
