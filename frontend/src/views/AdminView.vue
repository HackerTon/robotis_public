<script setup>
import CustomList from '@/components/CustomList.vue'
import { db } from '@/main'
import { collection, doc, orderBy, query, runTransaction } from 'firebase/firestore'
import { computed, ref, toRaw } from 'vue'
import { useCollection, useFirebaseAuth } from 'vuefire'

import { useWatchableRef } from '@/composable/helper'
import { useWebsocket } from '@/composable/websocket'
import { GAME_STATUS, GROUP_NAME, NAME_LIST, SCORE_MAP } from '@/constant'
import router from '@/router/index'

const auth = useFirebaseAuth()
const pendingGameRef = ref([])
const gameStatusRef = ref(GAME_STATUS.PRELIMINARY)

// Live scoreboard
const scoreBoardCollection = useCollection(
  query(collection(db, 'scores'), orderBy('score', 'desc')),
)

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
    scoresList.push({ id: key, name: NAME_LIST[key], millis: scoresObject[key][scoreLength - 1] })
  }
  return scoresList.sort((x, y) => {
    return x.score - y.score
  })
})

// Filtered group participants
const filteredScoreBoard = computed(() => {
  const filteredBasedOnGroup = [[], [], [], [], [], []]
  const thisScoreBoard = toRaw(scoreBoardCollection.value)

  if (gameStatusRef.value == GAME_STATUS.PRELIMINARY) {
    thisScoreBoard.sort((a, b) => {
      return a['millis'] - b['millis']
    })
  } else if (gameStatusRef.value == GAME_STATUS.LAPSE) {
    thisScoreBoard.sort((a, b) => {
      return b['score'] - a['score']
    })
  } else if (gameStatusRef.value == GAME_STATUS.FURTHERLAPSE) {
    thisScoreBoard.sort((a, b) => {
      return b['score'] - a['score']
    })
  }

  for (let i = 0; i != thisScoreBoard.length; ++i) {
    const groupType = i % 6
    filteredBasedOnGroup[groupType].push(thisScoreBoard[i])
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
  const currentArray = pendingGameRef.value

  try {
    await runTransaction(db, async (transaction) => {
      for (const [index, item] of currentArray.entries()) {
        const document = doc(db, 'scores', item['id'])
        let existingItem = scoreBoardCollection.value.find(
          (thisitem) => thisitem['id'] == item['name'],
        )

        let existingScore = existingItem == undefined ? 0 : existingItem['score']
        existingScore += SCORE_MAP[index + 1]
        if (gameStatusRef.value == GAME_STATUS.PRELIMINARY) {
          existingScore = index == 0 ? 1 : 0
        }

        transaction.set(document, {
          id: parseInt(item['id']),
          name: NAME_LIST[parseInt(item['id'])],
          score: existingScore,
          millis: item['millis'],
        })
      }
    })
    pendingGameRef.value = []
  } catch (error) {
    window.alert(error)
    console.error(error)
  }
}

// End game, push update to scoreboard
async function onEndGame() {
  await onUpdateScores()
}

// Update backend results into pending game
async function onUpdateGame() {
  // Push update to pendingGameRef
  for (const [index, item] of sortedWebsocketScores.value.entries()) {
    pendingGameRef.value.push(item)
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
      <div class="flex flex-col border-black border-2 rounded-lg">
        <div class="text-center mx-5 mb-2 p-3 font-bold text-2xl">Ranking List</div>
        <CustomList
          :data="scoreBoardCollection"
          :text="scoreboardLastUpdate"
          class="overflow-y-auto"
          use-score="true"
        />
      </div>

      <!-- COL 2 -->
      <div
        class="flex-none flex flex-col justify-between items-start border-black border-2 rounded-lg"
      >
        <div
          class="flex-none flex flex-row w-full items-start bg-slate-100 rounded-lg h-[60%] overflow-x-scroll"
        >
          <div v-for="(groupName, index) in GROUP_NAME" :key="groupName" class="w-[50vw]">
            <p>Group {{ groupName }}</p>
            <div v-for="({ id }, index) in filteredScoreBoard[index]" :key="id">
              <div>{{ index + 1 }}, {{ NAME_LIST[id] }}</div>
            </div>
          </div>
        </div>
        <div class="flex-none grid grid-cols-2 gap-2.5 p-5 w-full">
          <div class="col-span-2 flex flex-row">
            <p class="pr-2 flex-1">GameType</p>
            <select v-model="gameStatusRef" class="w-full border-2 flex-1">
              <option value="0">PRELIMINARY</option>
              <option value="1">LAPSE</option>
              <option value="2">FURTHERLAPSE</option>
            </select>
          </div>
          <div class="col-span-2">
            <p v-if="isSocketOpen">
              Websocket status: {{ isSocketOpen ? 'OPENED' : 'DISCONNECTED' }}
            </p>
            <p class="text-red-600" v-else>
              Websocket status: {{ isSocketOpen ? 'OPENED' : 'DISCONNECTED' }}
            </p>
          </div>
          <button
            @click="onEndGame"
            class="border-2 border-black py-3 px-4 shadow-md text-base rounded-md hover:bg-red-500 hover:ring-4 hover:cursor-auto"
          >
            END GAME
          </button>
          <button
            @click="onUpdateGame"
            class="border-2 border-black py-3 px-4 shadow-md text-base rounded-md hover:bg-red-500 hover:ring-4 hover:cursor-auto"
          >
            UPDATE GAME
          </button>
          <button
            @click="onClearLapse"
            class="border-2 border-black py-3 px-4 shadow-md text-base rounded-md hover:bg-red-500 hover:ring-4 hover:cursor-auto"
          >
            CLEAR LAPSE
          </button>
          <button
            @click="onSignout"
            class="border-2 border-black py-3 px-4 shadow-md text-base rounded-md hover:bg-red-500 hover:ring-4 hover:cursor-auto"
          >
            SIGNOUT
          </button>
        </div>
      </div>

      <!-- COL 3 -->
      <div class="flex flex-col border-black border-2 rounded-lg">
        <div class="flex-none overflow-y-auto h-[50%]">
          <div class="text-center pt-2.5 font-bold text-2xl">Backend Results</div>
          <CustomList :data="sortedWebsocketScores" :text="websocketLastUpdate" class="h-[50%]" />
        </div>
        <div class="flex-none overflow-y-auto h-[50%]">
          <div class="text-center pt-2.5 font-bold text-2xl">Pending Game</div>
          <CustomList :data="pendingGameRef" :text="websocketLastUpdate" />
        </div>
      </div>
    </div>
  </div>
</template>
