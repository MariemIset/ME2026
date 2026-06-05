<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class DatabaseSeeder extends Seeder
{
    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        // Static Users for Role-based Access
        User::updateOrCreate(['email' => 'ceo@airline.com'], [
            'name' => 'CEO',
            'password' => Hash::make('ceo123'),
            'role' => 'ceo',
        ]);

        User::updateOrCreate(['email' => 'marketing@airline.com'], [
            'name' => 'Marketing Team',
            'password' => Hash::make('marketing123'),
            'role' => 'marketing',
        ]);

        User::updateOrCreate(['email' => 'process@airline.com'], [
            'name' => 'Process Management',
            'password' => Hash::make('process123'),
            'role' => 'process',
        ]);

        // In a real scenario, we would also call seeders to parse the CSV files
        // $this->call([
        //     LoyaltyDataSeeder::class,
        //     SatisfactionDataSeeder::class,
        // ]);
    }
}
