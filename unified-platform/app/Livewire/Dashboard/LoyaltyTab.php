<?php

namespace App\Livewire\Dashboard;

use Livewire\Component;

class LoyaltyTab extends Component
{
    public function render()
    {
        return view('livewire.dashboard.loyalty-tab')->layout('components.layouts.app');
    }
}
