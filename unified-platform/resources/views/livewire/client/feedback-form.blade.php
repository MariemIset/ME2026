<div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-2xl mx-auto space-y-8 bg-white dark:bg-gray-800 p-10 rounded-2xl shadow-xl border border-gray-100 dark:border-gray-700">
        <div>
            <h2 class="text-3xl font-extrabold text-gray-900 dark:text-white text-center">
                Submit Your Feedback
            </h2>
            <p class="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
                Help us improve the ME2026 experience. Your opinion goes directly to our NLP sentiment engine.
            </p>
        </div>
        
        <form class="space-y-6">
            <div>
                <label for="feedback" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Your Experience</label>
                <div class="mt-1">
                    <textarea id="feedback" name="feedback" rows="4" class="shadow-sm focus:ring-rose-500 focus:border-rose-500 block w-full sm:text-sm border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md" placeholder="Tell us what you liked or didn't like..."></textarea>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Flight Class</label>
                    <select class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-rose-500 focus:border-rose-500 sm:text-sm rounded-md">
                        <option>Economy</option>
                        <option>Business</option>
                        <option>First Class</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Overall Rating (1-5)</label>
                    <input type="number" min="1" max="5" value="5" class="mt-1 block w-full shadow-sm focus:ring-rose-500 focus:border-rose-500 sm:text-sm border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md">
                </div>
            </div>

            <div>
                <button type="button" class="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gradient-to-r from-rose-600 to-rose-500 hover:from-rose-700 hover:to-rose-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-rose-500 transition-all">
                    Submit Feedback
                </button>
            </div>
            
            <div class="text-center mt-4 border-t border-gray-200 dark:border-gray-700 pt-4">
                <a href="{{ route('login') }}" class="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">Return to Employee Login</a>
            </div>
        </form>
    </div>
</div>
