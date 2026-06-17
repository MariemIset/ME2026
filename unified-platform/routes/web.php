<?php

use Illuminate\Support\Facades\Route;
use App\Livewire\Auth\Login;
use App\Livewire\Dashboard\ChurnTab;
use App\Livewire\Dashboard\LoyaltyTab;
use App\Livewire\Dashboard\SatisfactionTab;
use App\Livewire\Dashboard\NlpTab;
use App\Livewire\Client\FeedbackForm;

Route::get('/', Login::class)->name('login');

Route::middleware(['auth'])->group(function () {
    Route::get('/dashboard/churn', ChurnTab::class)->name('dashboard.churn');
    Route::get('/dashboard/loyalty', LoyaltyTab::class)->name('dashboard.loyalty');
    Route::get('/dashboard/satisfaction', SatisfactionTab::class)->name('dashboard.satisfaction');
    Route::get('/dashboard/nlp', NlpTab::class)->name('dashboard.nlp');
});

// Client portal for feedback
Route::get('/client/feedback', FeedbackForm::class)->name('client.feedback');
