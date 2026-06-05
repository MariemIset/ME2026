<div>
    <div class="max-w-2xl mx-auto py-12">
        <flux:card class="luxury-glass shadow-xl relative overflow-hidden">
            <!-- Decorative gradient orb -->
            <div class="absolute -top-10 -right-10 w-40 h-40 bg-indigo-500/10 rounded-full blur-3xl"></div>

            <div class="p-8 relative z-10">
                <flux:heading size="xl" class="mb-2 text-[#8c1d40]">Share Your Experience</flux:heading>
                <flux:text class="text-gray-500 mb-8">
                    Your feedback helps us improve our flights and services. Submit your comment below, and our automated systems will analyze your sentiment instantly.
                </flux:text>

                <form wire:submit="submit" class="space-y-6">
                    <flux:textarea 
                        wire:model="commentText" 
                        label="Your Comment" 
                        placeholder="Tell us about your flight, booking process, or overall experience..." 
                        rows="5"
                        class="bg-white/50 backdrop-blur-sm border-gray-200 focus:border-[#8c1d40] focus:ring-[#8c1d40]"
                    />

                    <div class="flex justify-end">
                        <flux:button type="submit" variant="primary" class="bg-[#8c1d40] hover:bg-[#6b1631] text-white transition-all magnetic-element">
                            <span wire:loading.remove wire:target="submit">Submit Feedback</span>
                            <span wire:loading wire:target="submit">Analyzing NLP...</span>
                        </flux:button>
                    </div>
                </form>

                <!-- Success State & Live NLP Digest -->
                @if ($successMessage)
                    <div class="mt-8 p-6 bg-green-50/80 border border-green-200 rounded-2xl backdrop-blur-md transition-all duration-500">
                        <div class="flex items-center gap-3 mb-3">
                            <flux:icon name="check-circle" class="text-green-600" />
                            <h3 class="font-bold text-green-900">{{ $successMessage }}</h3>
                        </div>
                        
                        @if ($analyzedSentiment)
                            <div class="mt-4 pt-4 border-t border-green-200/60">
                                <p class="text-sm font-semibold text-gray-700 mb-2">Live AI Analysis Digest:</p>
                                <div class="grid grid-cols-2 gap-4">
                                    <div class="bg-white/60 p-3 rounded-lg">
                                        <p class="text-xs text-gray-500 uppercase tracking-widest">Detected Sentiment</p>
                                        <p class="font-bold {{ $analyzedSentiment['sentiment'] === 'positive' ? 'text-green-600' : ($analyzedSentiment['sentiment'] === 'negative' ? 'text-red-600' : 'text-gray-600') }}">
                                            {{ ucfirst($analyzedSentiment['sentiment']) }}
                                        </p>
                                    </div>
                                    <div class="bg-white/60 p-3 rounded-lg">
                                        <p class="text-xs text-gray-500 uppercase tracking-widest">Polarity Score</p>
                                        <p class="font-bold text-gray-800">{{ number_format($analyzedSentiment['polarity'], 4) }}</p>
                                    </div>
                                </div>
                            </div>
                        @endif
                    </div>
                @endif

                @if ($errorMessage)
                    <div class="mt-8 p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">
                        {{ $errorMessage }}
                    </div>
                @endif
            </div>
        </flux:card>
    </div>
</div>
