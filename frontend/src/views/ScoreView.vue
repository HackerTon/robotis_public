<script setup>
import { useWatchableRef } from '@/composable/helper'
import { db } from '@/main'
import { collection, orderBy, query } from 'firebase/firestore'
import { generateFromString } from 'generate-avatar'
import { watch } from 'vue'
import { useCollection } from 'vuefire'
import AlertMP3 from '@/assets/alert.mp3'

const scores = useCollection(query(collection(db, 'scores'), orderBy('score', 'desc')))
const { lastUpdateText } = useWatchableRef(scores)


const alert = new Audio(AlertMP3)

watch(scores, () => {
  alert.play()
}, { deep: true })

function generateSVGFromText(text) { return `data:image/svg+xml;utf8,${generateFromString(text)}` }
</script>

<template>
  <div class="flex flex-col p-5 h-screen">
    <div class="flex-none grid place-content-center p-5">
      <div class="text-5xl font-semibold">2024 Competition Scoreboard</div>
    </div>
    <div class="flex-1 grid grid-cols-1 m-5 justify-items-center">
      <div class="flex flex-col w-[60vw]">
        <div class="flex-none text-center mx-5 mb-2 p-3 font-bold text-2xl">Ranking List</div>
        <div class="flex-none flex-col">
          <div class="text pb-2 justify-self-end">Last Update {{ lastUpdateText }}</div>
          <div class="grid grid-rows-1 gap-y-2.5">
            <div v-for="({ name, score }, index) in scores" :key="name"
              class="flex flex-row gap-5 bg-yellow-400 rounded-lg text-lg p-2.5 items-center">
              <div class="flex-initial">Ranking: {{ index + 1 }}</div>
              <img class="flex-initial h-10 w-10 rounded-full" :src="generateSVGFromText(name)" />
              <div class="flex-1">Player Name: {{ name }}</div>
              <div class="flex-1">Scores: {{ score }}</div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>
