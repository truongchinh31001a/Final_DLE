
export default function Home() {
  return (
    <div className="bg-gray-100 min-h-screen mt-20">
      {/* Header */}
      
      {/* Main content */}
      <main className="container mx-auto px-4 py-20 text-center">
        <h1 className="text-5xl font-bold text-gray-800 mb-6">
          Welcome to AI Diagnosis
        </h1>
        <p className="text-xl text-gray-600 mb-12">
          Revolutionizing the future of healthcare with advanced AI-powered diagnosis.
        </p>

        <div className="flex justify-center">
          <img
            src="/ai-diagnosis.png"
            alt="AI Diagnosis"
            className="w-3/4 max-w-2xl rounded-lg shadow-lg"
          />
        </div>

        <div className="mt-12">
          <h2 className="text-3xl font-semibold text-gray-800 mb-4">
            What We Do
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Our AI Diagnosis platform harnesses the power of cutting-edge machine learning models 
            to provide accurate, fast, and reliable medical diagnosis. Whether you're seeking 
            early detection or advanced insights into complex conditions, our AI is here to assist 
            medical professionals and improve patient outcomes.
          </p>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h3 className="text-2xl font-semibold text-gray-800 mb-2">Early Detection</h3>
            <p className="text-gray-600">
              Leverage AI for early detection of diseases to ensure timely treatment and better prognosis.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h3 className="text-2xl font-semibold text-gray-800 mb-2">Comprehensive Analysis</h3>
            <p className="text-gray-600">
              Our AI evaluates complex data to provide a comprehensive analysis, assisting doctors in making 
              informed decisions.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h3 className="text-2xl font-semibold text-gray-800 mb-2">Data-Driven Insights</h3>
            <p className="text-gray-600">
              Utilize data-driven insights from the AI to uncover trends and improve healthcare outcomes 
              for everyone.
            </p>
          </div>
        </div>

        <div className="mt-16">
          <button className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-all">
            Learn More
          </button>
        </div>
      </main>

      {/* Footer */}
      
    </div>
  );
}
