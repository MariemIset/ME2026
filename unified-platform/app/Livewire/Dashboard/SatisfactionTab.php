<?php

namespace App\Livewire\Dashboard;

use Livewire\Component;

class SatisfactionTab extends Component
{
    public function render()
    {
        return view('livewire.dashboard.satisfaction-tab')->layout('components.layouts.app');
    }
}
