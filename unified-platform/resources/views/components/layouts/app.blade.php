<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}" class="dark">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <title>{{ $title ?? 'ME2026 Unified Platform' }}</title>

        <!-- Fonts -->
        <link rel="preconnect" href="https://fonts.bunny.net">
        <link href="https://fonts.bunny.net/css?family=inter:400,500,600,700&display=swap" rel="stylesheet" />

        <!-- Tailwind CSS & Flux (Simulated with standard Tailwind config) -->
        @vite(['resources/css/app.css', 'resources/js/app.js'])
        @livewireStyles
    </head>
    <body class="font-sans antialiased bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex min-h-screen selection:bg-rose-500 selection:text-white transition-colors duration-200">
        
        <!-- Sidebar Navigation -->
        <livewire:dashboard.sidebar-filters />

        <!-- Main Content Area -->
        <main class="flex-1 p-6 md:p-8 ml-64 transition-all duration-300">
            <header class="flex justify-between items-center mb-8 border-b border-gray-200 dark:border-gray-800 pb-4">
                <div>
                    <h1 class="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-rose-700 to-rose-500">
                        {{ $heading ?? 'Dashboard Overview' }}
                    </h1>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Unified analytics and predictive insights for ME2026.</p>
                </div>
                
                <div class="flex items-center space-x-4">
                    <!-- User Profile / Logout (Static) -->
                    <div class="flex items-center gap-3 bg-white dark:bg-gray-800 rounded-full px-4 py-2 shadow-sm border border-gray-100 dark:border-gray-700">
                        <div class="w-8 h-8 rounded-full bg-rose-600 flex items-center justify-center text-white font-bold text-sm">
                            C
                        </div>
                        <span class="text-sm font-medium">CEO Login</span>
                    </div>
                </div>
            </header>

            <!-- Dynamic Livewire Content -->
            <div class="animate-fade-in-up">
                {{ $slot }}
            </div>
            
            <!-- Global Comments Drawer -->
            <livewire:dashboard.card-comments />
        </main>

        @livewireScripts
    </body>
</html>
