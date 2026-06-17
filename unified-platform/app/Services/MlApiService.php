<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;

class MlApiService
{
    protected string $mlApiUrl;
    protected string $nlpApiUrl;

    public function __construct()
    {
        $this->mlApiUrl = config('services.ml.url', 'http://localhost:8000');
        $this->nlpApiUrl = config('services.nlp.url', 'http://localhost:8002');
    }

    public function getChurnPredictions()
    {
        return Http::get("{$this->mlApiUrl}/predict/churn")->json();
    }

    public function getCustomerSegments()
    {
        return Http::get("{$this->mlApiUrl}/predict/segments")->json();
    }

    public function getSatisfactionScores()
    {
        return Http::get("{$this->mlApiUrl}/predict/satisfaction")->json();
    }

    public function analyzeSentiment(string $text)
    {
        return Http::post("{$this->nlpApiUrl}/analyze", [
            'text' => $text
        ])->json();
    }
}
