<?php

namespace App\Livewire\Auth;

use Livewire\Component;
use Illuminate\Support\Facades\Auth;

class Login extends Component
{
    public $email = '';
    public $password = '';

    public function login()
    {
        // Static auth for MVP
        if ($this->email == 'ceo@me2026.com') {
            // Mock login
            session(['user_role' => 'CEO']);
            return redirect()->route('dashboard.churn');
        } elseif ($this->email == 'marketing@me2026.com') {
            session(['user_role' => 'Marketing']);
            return redirect()->route('dashboard.churn');
        }

        $this->addError('email', 'Invalid credentials.');
    }

    public function render()
    {
        return view('livewire.auth.login')->layout('components.layouts.app');
    }
}
