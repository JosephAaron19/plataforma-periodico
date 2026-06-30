import { ArrowRight } from 'lucide-react';
import { useAuth } from '../contexts/auth';

export function CTASection() {
  const { isAuthenticated, openAuthModal } = useAuth();

  const handleSubscribeClick = () => {
    if (!isAuthenticated) {
      openAuthModal('register');
    } else {
      const plansSection = document.getElementById('planes');
      if (plansSection) {
        plansSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Fallback robust scroll using hash if scrollIntoView doesn't complete
        setTimeout(() => {
          const rect = plansSection.getBoundingClientRect();
          if (Math.abs(rect.top) > 50) {
            window.location.hash = 'planes';
          }
        }, 500);
      } else {
        window.location.hash = 'planes';
      }
    }
  };

  return (
    <section className="py-16 px-6 bg-gray-50">
      <div className="max-w-4xl mx-auto text-center">
        <div className="flex flex-col sm:flex-row items-center justify-center text-center sm:text-left gap-3 mb-6">
          <div className="w-12 h-12 rounded-full bg-white border-2 border-green-700 flex items-center justify-center flex-shrink-0">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1a4d2e" strokeWidth="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
          </div>
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-black text-slate-900 leading-tight">Mantente informado, estés donde estés</h2>
        </div>
        
        <p className="text-lg text-gray-600 mb-8">
          Únete a nuestra comunidad de lectores y recibe la mejor información de nuestra región.
        </p>

        <button 
          onClick={handleSubscribeClick}
          className="px-8 py-4 text-white rounded-lg text-lg flex items-center gap-2 mx-auto hover:opacity-90 transition-opacity cursor-pointer"
          style={{ backgroundColor: '#1a4d2e' }}
        >
          Quiero suscribirme ahora
          <ArrowRight size={24} />
        </button>
      </div>
    </section>
  );
}
