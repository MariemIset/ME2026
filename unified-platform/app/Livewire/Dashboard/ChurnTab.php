<?php

namespace App\Livewire\Dashboard;

use Livewire\Component;

class ChurnTab extends Component
{
    public function render()
    {
        return view('livewire.dashboard.churn-tab')->layout('components.layouts.app');
    }
}
