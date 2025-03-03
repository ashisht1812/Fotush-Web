import React from 'react';
import { Sparkles, Clock, DollarSign, Zap } from 'lucide-react';

const Features = () => {
  const features = [
    {
      icon: <Sparkles className="h-10 w-10 text-purple-600" />,
      title: 'AI-Powered Matching',
      description: 'Our intelligent algorithm connects you with photographers who match your style, budget, and location preferences.',
      color: 'from-purple-500 to-purple-600'
    },
    {
      icon: <Clock className="h-10 w-10 text-blue-600" />,
      title: 'On-Demand Bookings',
      description: 'Find available photographers near you in real-time for immediate or scheduled sessions.',
      color: 'from-blue-500 to-blue-600'
    },
    {
      icon: <DollarSign className="h-10 w-10 text-indigo-600" />,
      title: 'Flexible Pricing',
      description: 'Choose between per-session or per-minute pricing options to fit your specific needs and budget.',
      color: 'from-indigo-500 to-indigo-600'
    },
    {
      icon: <Zap className="h-10 w-10 text-pink-600" />,
      title: 'Instant Photo Delivery',
      description: 'Receive your professionally edited photos and videos quickly after your session through our secure platform.',
      color: 'from-pink-500 to-pink-600'
    }
  ];

  return (
    <section id="features" className="py-20 bg-gray-50 dark:bg-gray-800">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Why Choose Fotush</h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
            Experience the future of photography and videography services
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="bg-white dark:bg-gray-900 rounded-xl shadow-lg overflow-hidden transform transition-all hover:-translate-y-1 hover:shadow-xl">
              <div className="p-8">
                <div className="flex items-center mb-6">
                  <div className="p-3 rounded-lg bg-gradient-to-r from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700 mr-4">
                    {feature.icon}
                  </div>
                  <h3 className="text-2xl font-bold">{feature.title}</h3>
                </div>
                <p className="text-gray-600 dark:text-gray-400 text-lg">{feature.description}</p>
              </div>
              <div className="h-2 bg-gradient-to-r from-purple-600 to-blue-600"></div>
            </div>
          ))}
        </div>
        
        {/* Feature Highlight */}
        <div className="mt-16 bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl overflow-hidden shadow-xl">
          <div className="grid grid-cols-1 lg:grid-cols-2">
            <div className="p-8 lg:p-12 flex flex-col justify-center">
              <h3 className="text-3xl font-bold text-white mb-6">Elevate Your Photography Experience</h3>
              <p className="text-white/90 text-lg mb-8">
                With Fotush, you're not just booking a photographer – you're securing a premium experience with guaranteed quality, reliability, and satisfaction.
              </p>
              <button className="bg-white text-purple-600 hover:bg-gray-100 px-8 py-4 rounded-full font-bold shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1 self-start">
                Explore Premium Features
              </button>
            </div>
            <div className="relative h-64 lg:h-auto">
              <img 
                src="https://images.unsplash.com/photo-1516035069371-29a1b244cc32?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80" 
                alt="Professional photographer with camera" 
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Features;