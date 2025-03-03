import React from 'react';
import { Camera, DollarSign, Calendar, Users, CheckCircle } from 'lucide-react';

const PhotographerSignup = () => {
  const benefits = [
    {
      icon: <DollarSign className="h-5 w-5 text-green-500" />,
      text: 'Earn competitive rates on your schedule'
    },
    {
      icon: <Calendar className="h-5 w-5 text-green-500" />,
      text: 'Flexible booking system that works around your availability'
    },
    {
      icon: <Users className="h-5 w-5 text-green-500" />,
      text: 'Connect with clients looking for your specific skills'
    },
    {
      icon: <Camera className="h-5 w-5 text-green-500" />,
      text: 'Showcase your portfolio to thousands of potential clients'
    }
  ];

  return (
    <section className="py-20 bg-white dark:bg-gray-900 overflow-hidden relative">
      {/* Decorative Elements */}
      <div className="absolute top-0 left-0 w-64 h-64 bg-purple-200 dark:bg-purple-900/20 rounded-full -translate-x-1/2 -translate-y-1/2 opacity-50"></div>
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-200 dark:bg-blue-900/20 rounded-full translate-x-1/3 translate-y-1/3 opacity-50"></div>
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left Column - Image */}
          <div className="relative">
            <div className="rounded-2xl overflow-hidden shadow-2xl">
              <img 
                src="https://images.unsplash.com/photo-1554048612-b6a482bc67e5?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80" 
                alt="Photographer with camera" 
                className="w-full h-auto"
              />
            </div>
            
            {/* Floating Stats Card */}
            <div className="absolute -bottom-6 -right-6 bg-white dark:bg-gray-800 p-6 rounded-xl shadow-xl">
              <div className="flex items-center space-x-4">
                <div className="bg-purple-100 dark:bg-purple-900/30 p-3 rounded-full">
                  <Camera className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-gray-600 dark:text-gray-400">Join over</p>
                  <p className="text-2xl font-bold">5,000+ Photographers</p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Right Column - Content */}
          <div>
            <h2 className="text-3xl md:text-4xl font-bold mb-6">Turn Your Passion Into Profit</h2>
            <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
              Join Fotush as a photographer and connect with clients looking for your unique skills and style. Set your own rates, choose your schedule, and grow your business.
            </p>
            
            {/* Benefits List */}
            <div className="space-y-4 mb-8">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex items-center">
                  <div className="mr-3 bg-green-100 dark:bg-green-900/30 p-1 rounded-full">
                    {benefit.icon}
                  </div>
                  <p className="text-gray-700 dark:text-gray-300">{benefit.text}</p>
                </div>
              ))}
            </div>
            
            {/* CTA Button */}
            <button className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-full text-lg font-semibold transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1">
              Join as a Photographer
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PhotographerSignup;