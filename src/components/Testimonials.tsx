import React, { useState } from 'react';
import { Star, ChevronLeft, ChevronRight } from 'lucide-react';

const Testimonials = () => {
  const testimonials = [
    {
      id: 1,
      name: 'Sarah Johnson',
      role: 'Wedding Client',
      image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=256&q=80',
      quote: "Fotush made finding a last-minute wedding photographer so easy! The photographer was professional, talented, and delivered our photos within 48 hours. Couldn't be happier!",
      rating: 5,
      photoSample: 'https://images.unsplash.com/photo-1537633552985-df8429e8048b?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=500&q=80'
    },
    {
      id: 2,
      name: 'Michael Chen',
      role: 'Business Owner',
      image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=256&q=80',
      quote: "As a small business owner, I needed product photography on a budget. Fotush connected me with an amazing photographer who understood my vision perfectly. The results boosted my sales immediately!",
      rating: 5,
      photoSample: 'https://images.unsplash.com/photo-1531973486364-5fa64260d75b?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=500&q=80'
    },
    {
      id: 3,
      name: 'Emily Rodriguez',
      role: 'Travel Blogger',
      image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=256&q=80',
      quote: "I use Fotush in every city I visit. The platform makes it simple to book local photographers who know all the best spots. My Instagram has never looked better!",
      rating: 4,
      photoSample: 'https://images.unsplash.com/photo-1502791451862-7bd8c1df43a7?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=500&q=80'
    }
  ];

  const [activeIndex, setActiveIndex] = useState(0);

  const nextTestimonial = () => {
    setActiveIndex((prevIndex) => (prevIndex + 1) % testimonials.length);
  };

  const prevTestimonial = () => {
    setActiveIndex((prevIndex) => (prevIndex - 1 + testimonials.length) % testimonials.length);
  };

  return (
    <section id="testimonials" className="py-20 bg-gray-50 dark:bg-gray-800">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">What Our Users Say</h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
            Real stories from photographers and clients who use Fotush
          </p>
        </div>
        
        <div className="max-w-6xl mx-auto">
          {/* Testimonial Carousel */}
          <div className="relative">
            {/* Navigation Buttons */}
            <div className="absolute top-1/2 left-0 -translate-y-1/2 -translate-x-4 z-10 hidden md:block">
              <button 
                onClick={prevTestimonial}
                className="p-3 rounded-full bg-white dark:bg-gray-700 shadow-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
              >
                <ChevronLeft className="h-6 w-6 text-gray-700 dark:text-gray-300" />
              </button>
            </div>
            
            <div className="absolute top-1/2 right-0 -translate-y-1/2 translate-x-4 z-10 hidden md:block">
              <button 
                onClick={nextTestimonial}
                className="p-3 rounded-full bg-white dark:bg-gray-700 shadow-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
              >
                <ChevronRight className="h-6 w-6 text-gray-700 dark:text-gray-300" />
              </button>
            </div>
            
            {/* Testimonial Card */}
            <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl overflow-hidden">
              <div className="grid grid-cols-1 lg:grid-cols-2">
                {/* Left Column - Testimonial */}
                <div className="p-8 lg:p-12 flex flex-col justify-between">
                  {/* Quote */}
                  <div>
                    <div className="flex mb-6">
                      {[...Array(5)].map((_, i) => (
                        <Star 
                          key={i} 
                          className={`h-5 w-5 ${i < testimonials[activeIndex].rating ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300 dark:text-gray-600'}`} 
                        />
                      ))}
                    </div>
                    <p className="text-xl text-gray-700 dark:text-gray-300 italic mb-8">
                      "{testimonials[activeIndex].quote}"
                    </p>
                  </div>
                  
                  {/* Author */}
                  <div className="flex items-center">
                    <img 
                      src={testimonials[activeIndex].image} 
                      alt={testimonials[activeIndex].name} 
                      className="w-14 h-14 rounded-full object-cover mr-4"
                    />
                    <div>
                      <h4 className="font-bold text-lg">{testimonials[activeIndex].name}</h4>
                      <p className="text-gray-600 dark:text-gray-400">{testimonials[activeIndex].role}</p>
                    </div>
                  </div>
                </div>
                
                {/* Right Column - Image */}
                <div className="relative h-64 lg:h-auto">
                  <img 
                    src={testimonials[activeIndex].photoSample} 
                    alt="Photography sample" 
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-6">
                    <p className="text-white text-sm">Photo by Fotush Photographer</p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Mobile Navigation */}
            <div className="flex justify-center mt-8 space-x-2 md:hidden">
              {testimonials.map((_, index) => (
                <button 
                  key={index}
                  onClick={() => setActiveIndex(index)}
                  className={`w-3 h-3 rounded-full ${index === activeIndex ? 'bg-purple-600' : 'bg-gray-300 dark:bg-gray-600'}`}
                ></button>
              ))}
            </div>
          </div>
          
          {/* Gallery Preview */}
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              'https://images.unsplash.com/photo-1551854716-8b811be39e7e?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=600&q=80',
              'https://images.unsplash.com/photo-1604017011826-d3b4c23f8914?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=600&q=80',
              'https://images.unsplash.com/photo-1519741497674-611481863552?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=600&q=80',
              'https://images.unsplash.com/photo-1604268145635-5a2e0f150959?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=600&q=80'
            ].map((image, index) => (
              <div key={index} className="relative rounded-lg overflow-hidden group">
                <img 
                  src={image} 
                  alt={`Gallery image ${index + 1}`} 
                  className="w-full h-48 object-cover transition-transform duration-300 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end">
                  <div className="p-4">
                    <p className="text-white text-sm">Captured with Fotush</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default Testimonials;