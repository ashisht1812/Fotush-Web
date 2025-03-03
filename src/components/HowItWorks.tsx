import React from 'react';
import { Camera, Users, Calendar, Image } from 'lucide-react';

const HowItWorks = () => {
  const steps = [
    {
      icon: <Camera className="h-12 w-12 text-purple-600" />,
      title: 'Choose a Category',
      description: 'Select from ProClick, AeroLens, InstaPro, CineFrame, or ReelMakers based on your needs.',
      color: 'from-purple-500 to-purple-600'
    },
    {
      icon: <Users className="h-12 w-12 text-blue-600" />,
      title: 'Select a Photographer',
      description: 'Browse profiles, reviews, and pricing to find your perfect match.',
      color: 'from-blue-500 to-blue-600'
    },
    {
      icon: <Calendar className="h-12 w-12 text-indigo-600" />,
      title: 'Book & Pay Securely',
      description: 'Schedule your session and complete payment in seconds.',
      color: 'from-indigo-500 to-indigo-600'
    },
    {
      icon: <Image className="h-12 w-12 text-pink-600" />,
      title: 'Receive Photos & Videos',
      description: 'Get your professionally edited content delivered instantly.',
      color: 'from-pink-500 to-pink-600'
    }
  ];

  return (
    <section id="how-it-works" className="py-20 bg-white dark:bg-gray-900">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">How Fotush Works</h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
            Book your perfect photographer in just a few simple steps
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, index) => (
            <div key={index} className="relative">
              {/* Connector Line */}
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute top-16 left-full w-full h-0.5 bg-gradient-to-r from-gray-300 to-gray-300 dark:from-gray-700 dark:to-gray-700 z-0 -translate-y-1/2" style={{ width: 'calc(100% - 3rem)' }}></div>
              )}
              
              {/* Step Card */}
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 relative z-10 h-full transform transition-transform hover:-translate-y-2 hover:shadow-xl">
                {/* Step Number */}
                <div className="absolute -top-5 -left-5 w-10 h-10 rounded-full bg-gradient-to-r from-purple-600 to-blue-600 flex items-center justify-center text-white font-bold">
                  {index + 1}
                </div>
                
                {/* Icon */}
                <div className="mb-6 flex justify-center">
                  <div className="p-4 rounded-full bg-gradient-to-r from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800">
                    {step.icon}
                  </div>
                </div>
                
                {/* Content */}
                <h3 className="text-xl font-bold mb-3 text-center">{step.title}</h3>
                <p className="text-gray-600 dark:text-gray-400 text-center">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;