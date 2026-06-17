<?php

namespace App\Livewire\Client;

use Livewire\Component;

class FeedbackForm extends Component
{
    public function render()
    {
        return view('livewire.client.feedback-form')->layout('components.layouts.app');
    }
}
