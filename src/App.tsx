import React from 'react';
import { Camera, MapPin, Clock, CreditCard, Image, Search, ChevronRight, Star, CheckCircle } from 'lucide-react';
import Header from './components/Header';
import Footer from './components/Footer';
import HeroSection from './components/HeroSection';
import HowItWorks from './components/HowItWorks';
import Features from './components/Features';
import PhotographerSignup from './components/PhotographerSignup';
import Testimonials from './components/Testimonials';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 text-gray-800 dark:text-gray-100">
      <Header />
      <main>
        <HeroSection />
        <HowItWorks />
        <Features />
        <PhotographerSignup />
        <Testimonials />
      </main>
      <Footer />
    </div>
  );
}

export default App;