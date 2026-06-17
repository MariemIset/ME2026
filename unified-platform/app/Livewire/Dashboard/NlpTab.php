<?php

namespace App\Livewire\Dashboard;

use Livewire\Component;

class NlpTab extends Component
{
    public function render()
    {
        return view('livewire.dashboard.nlp-tab')->layout('components.layouts.app');
    }
}
