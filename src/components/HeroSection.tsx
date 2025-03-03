import React, { useState } from 'react';
import { MapPin, Search } from 'lucide-react';

const HeroSection = () => {
  const [location, setLocation] = useState('');

  return (
    <section className="relative py-20 md:py-32 overflow-hidden">
      {/* Background Image with Overlay */}
      <div className="absolute inset-0 z-0">
        <img 
          src="https://images.unsplash.com/photo-1542038784456-1ea8e935640e?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2070&q=80" 
          alt="Photographer in action" 
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-purple-900/70 to-blue-900/70"></div>
      </div>
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-3xl mx-auto text-center text-white">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
            Capture Every Moment with the Perfect Photographer – Instantly!
          </h1>
          <p className="text-xl md:text-2xl mb-8 text-gray-200">
            Book skilled photographers and videographers near you with ease.
          </p>
          
          {/* Search Bar */}
          <div className="bg-white/20 backdrop-blur-md p-2 rounded-full mb-8 max-w-xl mx-auto">
            <div className="flex items-center bg-white dark:bg-gray-800 rounded-full overflow-hidden">
              <div className="flex items-center pl-4 text-gray-500">
                <MapPin className="h-5 w-5" />
              </div>
              <input 
                type="text" 
                placeholder="Enter your location" 
                className="w-full py-3 px-4 outline-none text-gray-700 dark:text-gray-200 dark:bg-gray-800"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
              <button className="bg-purple-600 hover:bg-purple-700 text-white p-3 rounded-full m-1 transition-colors">
                <Search className="h-5 w-5" />
              </button>
            </div>
          </div>
          
          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <button className="px-8 py-4 bg-purple-600 hover:bg-purple-700 text-white rounded-full text-lg font-semibold transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1">
              Find a Photographer
            </button>
            <button className="px-8 py-4 bg-transparent hover:bg-white/10 border-2 border-white text-white rounded-full text-lg font-semibold transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1">
              Become a Photographer
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;