<script setup>
import CustomList from '@/components/CustomList.vue';
import { db } from '@/main';
import { collection, doc, orderBy, query, setDoc } from 'firebase/firestore';
import { computed, ref } from 'vue';
import { useCollection, useFirebaseAuth } from 'vuefire';

import { useWatchableRef } from '@/composable/helper';
import { useWebsocket } from '@/composable/websocket';
import { scoreMap, groupMap } from '@/constant';
import router from '@/router/index';

const auth = useFirebaseAuth()
const group = ref(0)


// Live scoreboard
const scoreBoardCollection = useCollection(query(collection(db, 'scores'), orderBy('score', 'desc')), { ssrKey: 'something' });
const { lastUpdateText: scoreboardLastUpdate } = useWatchableRef(scoreBoardCollection)

// Websocket
const { dataRef: jsonRef, isSocketOpen } = useWebsocket('ws://localhost:8000/ws')
const { lastUpdateText: websocketLastUpdate } = useWatchableRef(jsonRef)
const sortedWebsocketScores = computed(() => {
  if (jsonRef.value == null) return []
  const scoresObject = jsonRef.value

  const scoresList = []
  for (const key in scoresObject) {
    const scoreLength = scoresObject[key].length
    if (scoreLength == 0) continue
    // Only retain the latest score
    scoresList.push({ id: key, name: key, score: scoresObject[key][scoreLength - 1] })
  }
  return scoresList.sort((x, y) => {
    return x.score - y.score
  })
})

// Filtered group participants
const groupName = computed(() => groupMap[group.value])
const filteredScoreBoard = computed(() => {
  const filteredBasedOnGroup = [[], [], []]
  for (let i = 0; i != scoreBoardCollection.value.length; ++i) {
    const groupType = i % 3
    filteredBasedOnGroup[groupType].push(scoreBoardCollection.value[i])
  }
  return filteredBasedOnGroup
})

// Button callback
async function onSignout() {
  auth.signOut().then(() => router.push('/'))
}
async function onClearLapse() {
  try {
    const response = await fetch('http://localhost:8000/', { method: 'DELETE' })
    if (response.ok) {
      jsonRef.value = {}
    } else {
      console.error(response.statusText)
    }
  } catch (error) {
    console.error(error)
  }
}
async function onUpdateScores() {
  const currentArray = sortedWebsocketScores.value
  for (const [index, item] of currentArray.entries()) {
    const document = doc(db, 'scores', item['name'])
    let existingItem = scoreBoardCollection.value.find((thisitem) => thisitem['id'] == item['name'])
    let existingScore = existingItem == undefined ? 0 : existingItem['score']
    existingScore += scoreMap[index + 1]
    await setDoc(document, { 'id': parseInt(item['name']), 'name': item['name'], 'score': existingScore })
  }
}
</script>

<template>
  <div class="flex flex-col h-screen">
    <p class="flex-none grid place-content-center p-5 text-5xl font-semibold bg-yellow-100">
      2024 Competition Admin Panel
    </p>
    <div class="flex-1 grid grid-cols-1 md:grid-cols-3 m-5 gap-5">
      <!-- COL 1 -->
      <div class="flex-1 flex flex-col border-black border-2 rounded-lg">
        <div class="text-center mx-5 mb-2 p-3 font-bold text-2xl">Ranking List</div>
        <CustomList :data="scoreBoardCollection" :text="scoreboardLastUpdate" />
      </div>

      <!-- COL 2 -->
      <div class=" flex-1 flex flex-col border-black border-2 rounded-lg">
        <div class="text-center mx-5 mb-2 p-3 font-bold text-2xl">Group {{ groupName }} List</div>
        <CustomList :data="filteredScoreBoard[group]" :text="scoreboardLastUpdate" />
        <div class="grid grix-row-2 ">
          <div class="grid grid-cols-2 gap-2.5 p-5">
            <select v-model="group">
              <option value="0">GROUP A</option>
              <option value="1">GROUP B</option>
              <option value="2">GROUP C</option>
            </select>
            <p v-if="isSocketOpen">Websocket status: {{ isSocketOpen ? 'OPENED' : 'DISCONNECTED' }}</p>
            <p class="text-red-600" v-else>Websocket status: {{ isSocketOpen ? 'OPENED' : 'DISCONNECTED' }}</p>
            <button @click="onUpdateScores"
              class="border-2 border-black py-3 px-4 shadow-md text-base rounded-md hover:bg-red-500 hover:ring-4 hover:cursor-auto">
              UPDATE LAPSE
            </button>
            <button @click="onClearLapse"
              class="border-2 border-black py-3 px-4 shadow-md text-base rounded-md hover:bg-red-500 hover:ring-4 hover:cursor-auto">
              CLEAR LAPSE
            </button>
            <button @click="onSignout"
              class="border-2 border-black py-3 px-4 shadow-md text-base rounded-md hover:bg-red-500 hover:ring-4 hover:cursor-auto">
              SIGNOUT
            </button>
          </div>
        </div>
      </div>

      <!-- COL 3 -->
      <div class="flex-1 flex flex-col border-black border-2 rounded-lg">
        <div class="flex-none text-center mx-5 mb-2 p-3 font-bold text-2xl">Backend Lapse</div>
        <CustomList :data="sortedWebsocketScores" :text="websocketLastUpdate" class="flex-1" />
      </div>
    </div>
  </div>
</template>