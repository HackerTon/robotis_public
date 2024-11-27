<script setup>
defineProps(['data', 'text'])
</script>

<template>
    <div class="flex flex-col">
        <div class="text px-10 pb-1 self-end">Last Update {{ text }}</div>
        <div class="flex flex-col">
            <div v-for="({ name, score }, index) in data" :key="name"
                class="bg-yellow-400 mx-5 mb-4 p-3 rounded-lg text-lg flex flex-col md:flex-row md:items-center gap-x-5">
                <div class="flex-initial">Ranking: {{ index + 1 }}</div>
                <div class="flex-1">Player Name: {{ name }}</div>
                <div class="flex-1">Scores: {{ score }}</div>
            </div>
        </div>
    </div>
</template>