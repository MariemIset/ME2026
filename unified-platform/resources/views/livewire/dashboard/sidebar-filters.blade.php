<aside class="fixed inset-y-0 left-0 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 shadow-sm z-10 flex flex-col transition-transform duration-300">
    <div class="h-16 flex items-center justify-center border-b border-gray-200 dark:border-gray-700">
        <span class="text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-rose-700 to-rose-500 tracking-tighter">ME2026.</span>
    </div>
    
    <nav class="flex-1 overflow-y-auto py-6 px-4 space-y-2">
        <a href="{{ route('dashboard.churn') }}" class="{{ request()->routeIs('dashboard.churn') ? 'bg-rose-50 dark:bg-rose-900/20 text-rose-700 dark:text-rose-400 font-semibold' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white' }} group flex items-center px-3 py-2.5 text-sm font-medium rounded-xl transition-all duration-200">
            <svg class="mr-3 flex-shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            Churn Prediction
        </a>
        
        <a href="{{ route('dashboard.loyalty') }}" class="{{ request()->routeIs('dashboard.loyalty') ? 'bg-rose-50 dark:bg-rose-900/20 text-rose-700 dark:text-rose-400 font-semibold' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white' }} group flex items-center px-3 py-2.5 text-sm font-medium rounded-xl transition-all duration-200">
            <svg class="mr-3 flex-shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            Loyalty Segmentation
        </a>

        <a href="{{ route('dashboard.satisfaction') }}" class="{{ request()->routeIs('dashboard.satisfaction') ? 'bg-rose-50 dark:bg-rose-900/20 text-rose-700 dark:text-rose-400 font-semibold' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white' }} group flex items-center px-3 py-2.5 text-sm font-medium rounded-xl transition-all duration-200">
            <svg class="mr-3 flex-shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Satisfaction Scores
        </a>

        <a href="{{ route('dashboard.nlp') }}" class="{{ request()->routeIs('dashboard.nlp') ? 'bg-rose-50 dark:bg-rose-900/20 text-rose-700 dark:text-rose-400 font-semibold' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white' }} group flex items-center px-3 py-2.5 text-sm font-medium rounded-xl transition-all duration-200">
            <svg class="mr-3 flex-shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            NLP Sentiment
        </a>
    </nav>
    
    <div class="p-4 border-t border-gray-200 dark:border-gray-700">
        <div class="bg-rose-50 dark:bg-rose-900/10 rounded-xl p-4 border border-rose-100 dark:border-rose-900/30">
            <h4 class="text-xs font-semibold text-rose-800 dark:text-rose-300 uppercase tracking-wider mb-2">Global Filters</h4>
            
            <div class="space-y-3">
                <div>
                    <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Date Range</label>
                    <select class="w-full text-sm border-gray-300 dark:border-gray-600 dark:bg-gray-700 rounded-lg shadow-sm focus:ring-rose-500 focus:border-rose-500 py-1.5 text-gray-700 dark:text-gray-300">
                        <option>Last 30 Days</option>
                        <option>This Quarter</option>
                        <option>Year to Date</option>
                    </select>
                </div>
                <div>
                    <label class="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Customer Class</label>
                    <select class="w-full text-sm border-gray-300 dark:border-gray-600 dark:bg-gray-700 rounded-lg shadow-sm focus:ring-rose-500 focus:border-rose-500 py-1.5 text-gray-700 dark:text-gray-300">
                        <option>All Classes</option>
                        <option>Business</option>
                        <option>Economy</option>
                        <option>First Class</option>
                    </select>
                </div>
            </div>
        </div>
    </div>
</aside>
