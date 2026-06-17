<?php

namespace App\Livewire;

use Livewire\Component;
use Illuminate\Support\Facades\Http;
use App\Models\Comment;

class SubmitFeedback extends Component
{
    public $commentText = '';
    public $successMessage = '';
    public $errorMessage = '';
    public $analyzedSentiment = null;

    protected $rules = [
        'commentText' => 'required|min:10|max:1000',
    ];

    public function submit()
    {
        $this->validate();
        
        $this->successMessage = '';
        $this->errorMessage = '';
        $this->analyzedSentiment = null;

        try {
            // Forward to FastAPI NLP microservice
            $response = Http::post('http://fastapi_nlp:8000/analyze', [
                'reviews' => [
                    ['review' => $this->commentText, 'date' => now()->toDateString()]
                ]
            ]);

            if ($response->successful() && isset($response->json()['results'][0])) {
                $result = $response->json()['results'][0];
                $this->analyzedSentiment = $result;

                // Save comment locally for dashboard digest
                Comment::create([
                    'text' => $this->commentText,
                    'sentiment' => $result['sentiment'],
                    'polarity' => $result['polarity'],
                    'is_from_client' => true,
                ]);

                $this->successMessage = 'Thank you! Your feedback has been analyzed and submitted.';
                $this->commentText = ''; // Clear form
            } else {
                $this->errorMessage = 'Failed to analyze feedback. Please try again later.';
            }
        } catch (\Exception $e) {
            $this->errorMessage = 'Could not connect to the NLP engine: ' . $e->getMessage();
        }
    }

    public function render()
    {
        return view('livewire.submit-feedback')->layout('components.layouts.app');
    }
}
