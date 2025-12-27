<template>
  <div class="p-4 max-w-md mx-auto">
    <h1 class="text-2xl font-bold text-slate-900">Welcome, {{ userStore.profile.username }}</h1>
    
    <div class="grid grid-cols-2 gap-4 mt-6">
      <div class="bg-blue-50 p-4 rounded-xl shadow-sm">
        <p class="text-xs text-blue-600 font-semibold uppercase">Adherence</p>
        <p class="text-xl font-bold">{{ userStore.stats.adherence_rate }}%</p>
      </div>
      <div class="bg-green-50 p-4 rounded-xl shadow-sm">
        <p class="text-xs text-green-600 font-semibold uppercase">Active Items</p>
        <p class="text-xl font-bold">{{ userStore.pendingCount }}</p>
      </div>
    </div>

    <div class="mt-8">
      <h2 class="text-lg font-semibold mb-4 text-slate-700">Today's Focus (EXECUTE)</h2>
      <ul class="space-y-3">
        <li v-for="item in items" :key="item.id" class="flex items-center p-3 border rounded-lg">
           <input type="checkbox" @change="completeItem(item.id)" class="mr-3 h-5 w-5 text-indigo-600">
           <span>{{ item.title }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>